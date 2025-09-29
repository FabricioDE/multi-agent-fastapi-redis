import unittest
from unittest.mock import patch, MagicMock
from utils.llm_engine import AgentKnowledge

class TestAgentKnowledge(unittest.TestCase):

    def setUp(self):
        self.api_key = 'test_key'
        self.agent = AgentKnowledge(api_key=self.api_key)

    @patch('redis.Redis')
    def test_send_answer(self, mock_redis):
        mock_redis_instance = mock_redis.return_value

        self.agent.send_answer('response message', 123)

        mock_redis_instance.xadd.assert_called_once_with(
            "response_knowledge_stream", {"message": 'response message', "message_code": 123}
        )

if __name__ == '__main__':
    unittest.main()