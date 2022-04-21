import math
from typing import Dict, List
import pandas as pd
import numpy as np
import json
import time
import logging


class Param:

    def __init__(self,
                 N=0,
                 beta=0.5,
                 score=5,
                 window=10 * 60,
                 method="last") -> None:
        self.N = N
        self.beta = beta
        self.score = score
        self.window = window
        self.method = method


def ensure_timestamp(t, unit='s'):
    if unit == 's':
        if np.floor(t / 1000000000) < 10:
            return t
        else:
            return t // 1000


def _parse_param(**extra):
    param = Param()
    if extra.__contains__("N"):
        param.N = extra["N"]
    if extra.__contains__("beta"):
        param.beta = extra["beta"]
    if extra.__contains__("one_case_score"):
        param.one_case_score = extra["score"]
    if extra.__contains__("one_case_score"):
        param.window = extra["window"]
    if extra.__contains__("method"):
        param.method = extra["method"]
    return param


def merge_team_answer(answers):
    # construct team_res:{team_Id:[[create_time,cmdb_id,failure_type]]}
    team_res = {}
    for one_answer in answers:
        team_id = one_answer["teamId"]
        if not team_res.__contains__(team_id):
            team_res[team_id] = []
        try:
            content = json.loads(one_answer["content"])
        except:
            logging.error("提交格式错误，无法被json解析")
            continue
        if len(content) != 2:
            logging.error("提交格式错误，该提交为：\n" + json.dumps(one_answer))
            team_res[team_id].extend([-1] * 3)
            continue
        team_res[team_id].append(one_answer["createTime"])
        team_res[team_id].extend(content)
    return team_res


def score(reference, answers, delta, **extra):
    """
    Params:
        reference:{
            "timestamp":[],
            "cmdb_id":[],
            "failure_type":[]
        }

        answers:[
            {
                "teamId": id,
                "content": '[cmdb_id,failure_type]', 注意，content字段应为能被json解析的字符串而不是一个对象
                "createTime":13位时间戳
            }
        ]
        extra:非必传
            N: 提交预算窗口是故障案例的倍数，default 0，即不设预算窗口
            beta: delay系数下限， default 0.5
            score: 单题单项分数， default 5
            window: 算分的时间窗口， default 10min
    
    Return:
        各个团队每道题的得分 list
            [
                {
                    teamId: 1468883493088923650, // Number 19位 团队id
                    score: 20, // Number 该团队的最终得分
                    submitNum: 3, // Number 该团队的提交次数
                },
                ...
            ]
    """
    param = _parse_param(**extra)
    groundtruth = pd.DataFrame(reference)
    delta = int(delta) // 1000
    groundtruth["timestamp"] += delta

    # team_res = merge_team_answer(answers)
    groundtruth, answers_df = preprocess(groundtruth, answers)
    team_res = answers_df.groupby(by="team_id")
    team_score = []
    for team in team_res:
        final_score = cal_score_by_teams(groundtruth, team[1], param)
        team_score.append({
            "teamId": team[0],
            "score": sum(final_score),
            "submitNum": team[1].shape[0]
        })
    return team_score


def ts2date(ts):
    ts = int(ts // 1000)
    time_tuple = time.localtime(ts)
    return time.strftime("%Y-%m-%d-%H:%M:%S", time_tuple)


def cal_delay_score(t, real_t, param, unit='m'):
    if real_t - t > param.window:
        return 0
    if unit == 'm':
        delay = math.floor((real_t - t) / 60)
        delay = max(delay, 0)
        return max(min((10 - delay) / 10, 1) * (1 - param.beta), 0) + param.beta
    raise ValueError("unit must be 'm'")


def cal_score_by_teams(groundtruth, answer, param):
    """
    groundtruth:["timestamp","cmdb_id","failure_type"]
    k:预算倍数
    method:针对同一case的多次提交，如何计算分
    beta:在第10分钟检测出来故障的delay系数
    """
    answer = answer.sort_values(by="timestamp")
    if param.N > 0:
        split = int(np.floor(groundtruth.shape[0] * param.N))
        answer = answer.iloc[:split]
    result = []
    for i in groundtruth.index:
        one_case_result = 0
        c = groundtruth.loc[i]
        t = c["timestamp"]
        tmp = answer[(answer["timestamp"] >= t - 59) &
                     (answer["timestamp"] <= t + param.window)]
        if tmp.empty:
            result.append(0)
            continue
        one_case_result = _cal_score(c, tmp, param)
        result.append(one_case_result)
    return result


def _cal_score(cases, ans, param):
    t = cases["timestamp"]
    cmdb = cases["cmdb_id"]
    label = cases["failure_type"]
    r = []
    for j in ans.index:
        one_case_result = 0
        one_anomaly_result = 0
        a = ans.loc[j]
        delay_score = cal_delay_score(t, a["timestamp"], param)
        if a["cmdb_id"] == cmdb:
            one_anomaly_result += param.score
            one_case_result += param.score
        if a["failure_type"] == label:
            one_case_result += param.score
        one_case_result *= delay_score
        r.append(one_case_result)
    if not r:
        return 0
    if param.method == "last":
        res = r[-1]
    elif param.method == "max":
        res = max(r)
    else:
        res = r[-1]
    return res


def answers_to_df(answers):
    new_ans = []
    for one_answer in answers:
        one_new_ans = [one_answer["teamId"], (one_answer["createTime"])]
        try:
            content = json.loads(one_answer["content"])
        except:
            logging.error("提交格式错误，无法被json解析")
            continue
        if len(content) != 2:
            logging.error("提交格式错误，该提交为：\n" + json.dumps(one_answer))
            content = ["error submit", "error submit"]
            continue
        one_new_ans.extend(content)
        new_ans.append(one_new_ans)
    df = pd.DataFrame(
        new_ans, columns=["team_id", "timestamp", "cmdb_id", "failure_type"])
    df["timestamp"] = df["timestamp"].astype(np.int64).apply(ensure_timestamp)
    return df


def preprocess(gt, answers, threshold=10 * 60):
    '''丢弃故障间隔小于10min的故障及提交'''
    gt = gt.sort_values(by="timestamp").reset_index(drop=True)
    intervals = np.diff(gt["timestamp"].values, prepend=0)
    index = np.where(intervals <= threshold)[0]
    new_answers = answers_to_df(answers)
    if index.shape[0] <= 0:
        return gt, new_answers
    index0 = index - 1

    start = gt["timestamp"].values[index0]
    end = gt["timestamp"].values[index] + threshold
    for i in range(start.shape[0]):
        new_answers = new_answers[(new_answers["timestamp"] < start[i]) |
                                  (new_answers["timestamp"] > end[i])]
    drop_index=np.concatenate((index0, index))
    print(gt.iloc[sorted(drop_index)])
    gt = gt.drop(drop_index, axis=0).reset_index(drop=True)
    print(f"drop {len(index)*2} cases")
    
    return gt, new_answers




if __name__ == "__main__":
    ground_truth = pd.read_csv("result_sample.csv")
    answers = []
    with open("result.json") as f:
        answers = json.load(f)
    res = score(
        {
            "timestamp": ground_truth["timestamp"].values.tolist(),
            "cmdb_id": ground_truth["cmdb_id"].values.tolist(),
            "failure_type": ground_truth["failure_type"].values.tolist()
        },
        answers,
        0,
        method="last",
    )
    res = sorted(res, key=lambda r: int(r["teamId"]))
    print(res)
