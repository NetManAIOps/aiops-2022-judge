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


## 获取数据脚本样例

### 环境准备

` pip install kafka-python `

### 样例

```python
import json

from kafka import KafkaConsumer

AVAILABLE_TOPICS = {
    'kpi-27433a60a55e4a1745ad77acfd4038c1',
    'metric-27433a60a55e4a1745ad77acfd4038c1',
    'trace-27433a60a55e4a1745ad77acfd4038c1',
    'log-27433a60a55e4a1745ad77acfd4038c1'
}

CONSUMER = KafkaConsumer(
    'kpi-27433a60a55e4a1745ad77acfd4038c1',
    'metric-27433a60a55e4a1745ad77acfd4038c1',
    'trace-27433a60a55e4a1745ad77acfd4038c1',
    'log-27433a60a55e4a1745ad77acfd4038c1',
    bootstrap_servers=['10.3.2.41', '10.3.2.4', '10.3.2.36'],
    auto_offset_reset='latest',
    enable_auto_commit=False,
    security_protocol='PLAINTEXT'
)


def main():
    """Consume data and react"""
    assert AVAILABLE_TOPICS <= CONSUMER.topics(), 'Please contact admin'
    print('test consumer')
    i = 0
    for message in CONSUMER:
        i += 1
        data = json.loads(message.value.decode('utf8'))
        timestamp = data['timestamp']
        print(i, message.topic, timestamp)
        if 'log' in message.topic:
            print(data['value'])


if __name__ == '__main__':
    '''
        start to consume kafka
    '''
    main()

```

## 提交答案脚本样例

### 环境准备

` pip install requests `

```python
import json

import requests

# 提交答案服务域名或IP, 将在赛前告知
HOST = "answer service host"
# 团队标识, 可通过界面下方权限获取, 每个ticket仅在当前赛季有效，如未注明团队标识，结果不计入成绩
TICKET = "your team ticket"


def submit(ctx):
    assert (isinstance(ctx, list))
    assert (len(ctx) == 2)
    assert (isinstance(ctx[0], str))
    assert (isinstance(ctx[1], str))
    data = {'content': json.dumps(ctx, ensure_ascii=False)}
    r = requests.post(
        url='%s/answer/submit' % HOST,
        json=data,
        headers={"ticket": TICKET}
    )
    return r.text


if __name__ == '__main__':
    '''
        test part
    '''
    res = submit(["adservice", "k8s容器CPU压力"])
    print(res)
    # {"code":0,"msg":"","data":1} 成功提交一次答案

```