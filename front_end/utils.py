import json

# 读取配置文件
def read_config(config_file: str) -> dict:
    """
    读取指定路径的配置文件并返回配置对象

    参数:
    config_file (str): 配置文件的名称

    返回:
    dict: 包含配置信息的字典对象
    """
    
    with open(config_file, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config

# 写入配置文件
def write_config(config_file: str, config: dict):
    """
        将配置信息写入到指定的文件中。
        
        参数:
        config_file (str): 配置文件的路径和名称。
        config (dict): 包含配置信息的字典。
        
        返回:
        无
    """
    with open(config_file, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)

# 更新配置文件
def update_config(config_file: str, **kwargs):
    """
    动态更新配置文件中的参数。
    
    该函数接受任意关键字参数，每个关键字参数代表配置文件中的一个设置项。
    它会读取当前的配置文件，然后用传入的参数更新配置文件中的设置项。
    
    参数:
    **kwargs: 关键字参数，包含需要更新的配置项及其新值。
    
    返回:
    无
    """   
    config = read_config(config_file)    
    config.update(kwargs)    
    write_config(config_file, config)
    
# 获取更新后的配置
def get_updated_config(config: dict, **kwargs):
    """
    读取一个配置文件，并根据传入的关键字参数更新配置
    
    参数:
    config: 配置字典，用于读取初始配置
    **kwargs: 一个或多个关键字参数，用于更新配置
    
    返回值:
    返回一个字典，包含更新后的配置
    """
    config.update(kwargs)    
    return config
    