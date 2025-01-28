import os
import fnmatch
import shutil
    
def find_files(dir, extensions):
    """
    遍历指定目录及其子目录，查找具有指定扩展名的文件。

    :param directory: 要搜索的根目录。
    :param extensions: 一个包含所需文件扩展名的列表或元组。
    :return: 包含匹配文件路径的生成器。
    """
    for root, dirnames, filenames in os.walk(dir):
        for ext in extensions:
            for filename in fnmatch.filter(filenames, f'*{ext}'):
                # yield filename and its path in the directory
                yield filename, os.path.join(root, filename)
                
def copy_and_rename_file(src_file_path, tar_dir, new_name):
    """
    复制一个文件到指定工作目录并重命名。
    
    :param src_file_path: 源文件路径（包括文件名和扩展名）。
    :param new_name: 新文件的名字（包括扩展名）。
    """
     # 若找不到目标文件夹，则创建它
    if not os.path.exists(tar_dir):
        os.makedirs(tar_dir)
    
    # 构建目标文件路径（即复制后的文件路径）
    temp_dest_path = os.path.join(tar_dir, os.path.basename(src_file_path))
    
    # 复制文件到当前目录
    shutil.copy(src_file_path, temp_dest_path)
    
    # 构建新的文件名路径
    new_file_path = os.path.join(tar_dir, new_name)
    
    # 如果新文件名与原文件名不同，则进行重命名
    if temp_dest_path != new_file_path:
        os.rename(temp_dest_path, new_file_path)
