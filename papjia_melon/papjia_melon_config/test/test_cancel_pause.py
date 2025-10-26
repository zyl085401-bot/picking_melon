import time
import rclpy
from rclpy.node import Node
from papjia_behavior_interface.srv import TriggerSignal
import argparse

class ServiceClient(Node):
    def __init__(self):
        super().__init__('test_cancel_pause_client')
        self.cli = self.create_client(TriggerSignal, '/pause_until_signal')
        
    def send_request(self, signal_id):
        req = TriggerSignal.Request()
        req.signal_id = signal_id
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--signal_id', help='Signal identifier')
    args = parser.parse_args()
    
    rclpy.init()
    client = ServiceClient()
    try:
        time.sleep(1.0)
        response = client.send_request(args.signal_id)
        print(f'Service call succeeded: {response}')
    except Exception as e:
        print(f'Service call failed: {e}')
    finally:
        client.destroy_node()
        rclpy.shutdown()