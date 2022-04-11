# aiops-2022-judge

2022挑战赛评测脚本

## 评测脚本使用样例

### 环境准备

`pip3 install -r requirements.txt`

### 方式一：使用`judge_cli`

`python3 judge_cli.py -gt "result_sample.csv" -r "result.json"`

参数说明：

```
-gt 后面接ground_truth file path
-r 后面接answer file path
```

### 方式二：直接调用`score`函数

`judge.py` 文件的 `score` 为计算分数的函数，具体调用方式如下所示

```python
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
    method="max",
)
res = sorted(res, key=lambda r: int(r["teamId"]))
```

**注意**: 提交时，`content`字段应为可被json解析的字符串。
如

```json
{
    "teamId": "1",
    "content": "[\n  \"emailservice-0\",\n  \"k8s容器写io负载\"\n]",
    "createTime": 1647274990
}
```

而非

```json
{
    "teamId": "1",
    "content": [
        "emailservice-0",
        "k8s容器写io负载"
    ],
    "createTime": 1647274990
}
```

**对象转化成json字符串方式**

```python
import json

x = ["emailservice-0","k8s容器写io负载"]

x_string = json.dumps(x,ensure_ascii=True)
```
