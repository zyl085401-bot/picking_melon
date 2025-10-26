# 设计思路
- 提供使用python构造并执行行为树的功能
    - ```action_models.py``` 文件提供加载原子动作模型的功能，并能够生成原子技能的python代码【生成继承 ```ActionNode``` 的原子动作】
    - ```btree.py``` 提供嵌套构造行为树的能力【可构造多个行为树】
    - ```executor.py``` 提供执行行为树的能力【需指定行为树内容（可包含多个行为树）以及要执行的行为树的名称】
- 提供原子动作模型以供前端设计行为树，并接受前端的行为树信息并执行【与前端交互的功能需要后续开发】
    - ```action_models.py``` 文件提供加载原子动作模型的功能
    - ```executor.py``` 提供执行行为树的能力【需指定行为树内容（可包含多个行为树）以及要执行的行为树的名称】

# 测试【python】
- 运行 ```action_models.py``` 以生成原子动作
    - 需要配置 ```papjia_skill/config/action_model.yaml``` 中的 ```action_dirs```
- 执行 ```colcon build``` 和 ```source install/setup.bash``` 以正确加载原子动作
- 加载行为树的Server【如 ```papjia_object_manage/object_manage_behaviors/launch/bt_loader.launch.py```】
- 生成自己的行为树并执行【参见 ```papjia_skill/test/test.py```】
    - 参考 ```create_tree``` 函数构造您的行为树
