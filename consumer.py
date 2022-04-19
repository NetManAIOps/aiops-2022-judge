"""
Example for data consuming.

Before running this script, execute

    pip3 install kafka-python
"""
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
        print(type(data), data)


if __name__ == '__main__':
    '''
        start to consume kafka
    '''
    main()
