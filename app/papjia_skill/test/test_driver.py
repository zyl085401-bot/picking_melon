import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from papjia_behavior_interface.action import ExecuteTree
from papjia_skill.executor import PapjiaSkillExecutor
from papjia_skill.btree import BehaviorRoot, BehaviorTree, Sequence, Parallel, SubTree
from papjia_skill.action_models import ActionModels
from papjia_skill.atom.remove_escape_character import RemoveEscapeCharacter
from papjia_skill.atom.papjia_delay_async import PapjiaDelayAsync
from papjia_skill.atom.gripper_command import GripperCommand
from papjia_skill.atom.set_do import SetDO
from papjia_skill.atom.dish_transfer_command import DishTransferCommand
from papjia_skill.atom.pipette_command import PipetteCommand

server_topics = {
    "right_gripper": "/szyj_driver/right_hand_controller/gripper_cmd",
    "left_p_gripper": "/szyj_driver/left_hand_p_controller/gripper_cmd",
    "left_r_gripper": "/szyj_driver/left_hand_r_controller/gripper_cmd",
    "slide": "/szyj_driver/flask_clamping_slide_controller/gripper_cmd",
    "pump1": "/szyj_driver/pump1_controller/pump_out",
    "pump2": "/szyj_driver/pump2_controller/pump_out",
    "pump3": "/szyj_driver/pump3_controller/pump_out",
    "pipette1": "/szyj_driver/pipette1_controller/command",
    "pipette10": "/szyj_driver/pipette10_controller/command",
    "dish_transfer": "/szyj_driver/dish_transfer_controller/command",
    "storage": "/dish_storage/action",
    "set_do": "/szyj_driver/gpio_controller/set_do",
}


def swap_quotes(input_str):
    # 使用占位符替换单引号
    temp_str = input_str.replace("'", "$PH")
    # 将双引号转换为单引号
    temp_str = temp_str.replace('"', "'")
    # 将占位符替换回双引号
    result_str = temp_str.replace("$PH", '"')
    return result_str


def seq_right_gripper(name="SeqRightGripper"):
    actions = {}
    actions["延迟1秒"] = PapjiaDelayAsync(
        delay_duration=1.0,
    )
    actions["开右爪"] = GripperCommand(
        action_name=server_topics["right_gripper"],
        goal_position=700,
        force=20,
        velocity=50,
    )
    actions["关右爪"] = GripperCommand(
        action_name=server_topics["right_gripper"],
        goal_position=1,
        force=50,
        velocity=50,
    )
    actions["右爪微开"] = GripperCommand(
        action_name=server_topics["right_gripper"],
        goal_position=400,
        force=10,
        velocity=50,
    )
    actions["右爪微关"] = GripperCommand(
        action_name=server_topics["right_gripper"],
        goal_position=100,
        force=5,
        velocity=50,
    )
    seq = Sequence(name)
    seq.add_child(actions["开右爪"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["关右爪"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["右爪微开"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["右爪微关"])
    seq.add_child(actions["延迟1秒"])
    return seq


def seq_left_p_gripper(name="SeqLeftPGripper"):
    actions = {}
    actions["延迟1秒"] = PapjiaDelayAsync(
        delay_duration=1.0,
    )
    actions["左爪放松的夹"] = GripperCommand(
        action_name=server_topics["left_p_gripper"],
        goal_position=450,
        force=10,
        velocity=50,
    )
    actions["关左爪"] = GripperCommand(
        action_name=server_topics["left_p_gripper"],
        goal_position=1000,
        force=50,
        velocity=50,
    )
    actions["开左爪"] = GripperCommand(
        action_name=server_topics["left_p_gripper"],
        goal_position=150,
        force=20,
        velocity=50,
    )
    actions["玻璃试管开左爪"] = GripperCommand(
        action_name=server_topics["left_p_gripper"],
        goal_position=300,
        force=20,
        velocity=50,
    )
    actions["玻璃试管关左爪"] = GripperCommand(
        action_name=server_topics["left_p_gripper"],
        goal_position=1000,
        force=20,
        velocity=50,
    )
    seq = Sequence(name)
    seq.add_child(actions["开左爪"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["左爪放松的夹"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["关左爪"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["玻璃试管开左爪"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["玻璃试管关左爪"])
    seq.add_child(actions["延迟1秒"])
    return seq


def seq_left_r_gripper(name="SeqLeftRGripper"):
    actions = {}
    actions["延迟1秒"] = PapjiaDelayAsync(
        delay_duration=1.0,
    )
    actions["归零旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=0,
        force=20,
        velocity=50,
    )
    actions["试管架旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=45,
        force=20,
        velocity=50,
    )
    actions["放盖旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=90,
        force=20,
        velocity=50,
    )
    actions["开盖旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=450,
        force=80,
        velocity=50,
    )
    actions["关盖旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=-1000,
        force=50,
        velocity=40,
    )
    actions["扫码正旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=100,
        force=50,
        velocity=40,
    )
    actions["扫码反旋转"] = GripperCommand(
        action_name=server_topics["left_r_gripper"],
        goal_position=-100,
        force=50,
        velocity=40,
    )
    seq = Sequence(name)
    seq.add_child(actions["归零旋转"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["试管架旋转"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["放盖旋转"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["开盖旋转"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["关盖旋转"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["扫码正旋转"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["扫码反旋转"])
    seq.add_child(actions["延迟1秒"])
    return seq


def seq_slide(name="SeqSlide"):
    actions = {}
    actions["延迟1秒"] = PapjiaDelayAsync(
        delay_duration=1.0,
    )
    actions["伸滑台"] = GripperCommand(
        action_name=server_topics["slide"],
        goal_position=2800,
        force=20,
        velocity=20,
    )
    actions["缩滑台"] = GripperCommand(
        action_name=server_topics["slide"],
        goal_position=0,
        force=20,
        velocity=50,
    )
    seq = Sequence(name)
    seq.add_child(actions["伸滑台"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["缩滑台"])
    seq.add_child(actions["延迟1秒"])
    return seq


def seq_pipette1(name="SeqPipette1"):
    actions = {}
    actions["延迟1秒"] = PapjiaDelayAsync(
        delay_duration=1.0,
    )
    actions["1ml枪吸液"] = PipetteCommand(
        action_name=server_topics["pipette1"],
        command="aspirate",
        value=1.0,
    )
    actions["1ml枪吐液"] = PipetteCommand(
        action_name=server_topics["pipette1"],
        command="dispense",
        value=1.0,
    )
    actions["1ml枪弹枪头"] = PipetteCommand(
        action_name=server_topics["pipette1"],
        command="eject_tip",
        value=0.0,
    )
    actions["1ml枪激活"] = PipetteCommand(
        action_name=server_topics["pipette1"],
        command="activate",
        value=0.0,
    )
    seq = Sequence(name)
    seq.add_child(actions["1ml枪激活"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪吸液"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪吐液"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪吸液"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪吐液"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪吸液"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪吐液"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["1ml枪弹枪头"])
    seq.add_child(actions["延迟1秒"])
    return seq


def seq_gpio(name="SeqGPIO"):
    actions = {}
    actions["延迟1秒"] = PapjiaDelayAsync(
        delay_duration=1.0,
    )
    actions["开振荡器"] = SetDO(
        service_name=server_topics["set_do"], names="shaker", values="0"
    )
    actions["关振荡器"] = SetDO(
        service_name=server_topics["set_do"], names="shaker", values="1"
    )
    actions["开吸盘"] = SetDO(
        service_name=server_topics["set_do"], names="suction", values="0"
    )
    actions["关吸盘"] = SetDO(
        service_name=server_topics["set_do"], names="suction", values="1"
    )

    seq = Sequence(name)
    seq.add_child(actions["开振荡器"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["关振荡器"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["开吸盘"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["关吸盘"])
    seq.add_child(actions["延迟1秒"])
    return seq


def tree_test_main(tree_name="TestDriverMain"):
    # seq = Sequence("SeqMain")
    seq = Parallel("ParallelSeqMain")
    # seq.add_child(seq_right_gripper())
    # seq.add_child(seq_left_p_gripper())
    # seq.add_child(seq_left_r_gripper())
    # seq.add_child(seq_slide())
    seq.add_child(seq_gpio())
    tree = BehaviorTree(tree_name)
    tree.add_child(seq)
    root = BehaviorRoot()
    root.add_child(tree)
    return tree_name, root.to_str()


def tree_test_pipette(tree_name="TestPipette"):
    seq = Sequence("SeqPipette")
    seq.add_child(seq_pipette1())
    tree = BehaviorTree(tree_name)
    tree.add_child(seq)
    root = BehaviorRoot()
    root.add_child(tree)
    return tree_name, root.to_str()


def tree_test_qc(tree_name="TestQC"):
    actions = {}
    actions["快换上电"] = SetDO(
        service_name=server_topics["set_do"], names=["qc_power"], values=[float(1)]
    )
    actions["延迟1秒"] = PapjiaDelayAsync(delay_duration=1.0)
    actions["快换松1"] = SetDO(
        service_name=server_topics["set_do"], names=["qc_release"], values=[float(0)]
    )
    actions["快换锁1"] = SetDO(
        service_name=server_topics["set_do"], names=["qc_lock"], values=[float(0)]
    )
    actions["快换锁2"] = SetDO(
        service_name=server_topics["set_do"], names=["qc_lock"], values=[float(1)]
    )
    actions["快换松2"] = SetDO(
        service_name=server_topics["set_do"], names=["qc_release"], values=[float(1)]
    )
    actions["快换断电"] = SetDO(
        service_name=server_topics["set_do"], names=["qc_power"], values=[float(0)]
    )
    seq = Sequence("SeqQC")
    seq.add_child(actions["快换上电"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["快换松1"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["快换锁1"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["快换锁2"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["快换松2"])
    seq.add_child(actions["延迟1秒"])
    seq.add_child(actions["快换断电"])
    tree = BehaviorTree(tree_name)
    tree.add_child(seq)
    root = BehaviorRoot()
    root.add_child(tree)
    return tree_name, root.to_str()


def main(args=None):
    rclpy.init(args=args)
    executor = PapjiaSkillExecutor()

    models = ActionModels(
        "/workspace/src/papjia_skill/config/action_model.yaml"
    )  # 需要显式加载原子动作模型以检查字段
    tree_id, tree_str = tree_test_main()
    # tree_id, tree_str = tree_test_qc()
    # tree_id, tree_str = tree_test_pipette()
    tree_str = swap_quotes(tree_str)
    print(tree_str)

    try:
        executor.execute_tree(tree_string=tree_str, tree_name=tree_id)
    except ValueError as e:
        executor.get_logger().error(f"错误: {e}")
    except Exception as e:
        executor.get_logger().error(f"未知错误: {e}")
    finally:
        executor.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
