# Anime Subtitle Renamer

<p align="center">
    <img title="SubtitleRenamer" src="docs/preview/config_editor.png" alt="" width=50%>
</p>

该项目的功能是根据给定视频文件匹配本地字幕并重命名字幕文件，亮点在于可以使用**大模型**自动识别文件中的集数信息，通用性比一般正则表达式强很多！有一个勉强能用的GUI界面。

## 初衷

在使用TinyMediaManager刮削并重命名动画文件之后，视频文件和下载的字幕文件将无法匹配；人工重命名大量文件过于麻烦，所以搭建了一个自动化流程来处理这件事。
本项目的默认集数匹配规则（ab）来源于[AutoBangumi](https://github.com/EstrellaXD/Auto_Bangumi)，因此可能不适用于非动画文件、非动画字幕组的重命名工作。
若想实现更加通用的字幕匹配，推荐使用**ai**模式并配置大模型的`Base URL`、`API Key`和`Model Name`，实现基于大模型的文件匹配。

## Anime Subtitle Renamer功能简介

- 根据给定文件夹地址中视频名自动匹配对应字幕文件并进行重命名，输出至指定文件夹
- 支持自定义字幕语言后缀的映射
- 支持自定义匹配的视频、字幕格式
- 支持三种视频-字幕匹配方法
- 可自动清除视频文件夹中的旧字幕文件

## 视频和字幕文件目录说明

Anime Subtitle Renamer可以读取的视频所在目录需满足以下要求：

- 视频文件保存在同一目录下
- 视频所在目录没有其他视频文件干扰
- 视频所在目录的子文件夹中允许存在其他视频文件
- 视频文件有集数标识，如`孤独摇滚！ - S01E01 - 孤独的转机.mkv`或`[DMG&VCB-Studio] BOCCHI THE ROCK! [06][Ma10p_1080p][x265_flac].mkv`
- 不支持合集，如`A E01-04.mp4`
- 示例视频所在目录结构如下：

```file
    video_dir
    ├── A S01E01.mp4
    ├── A S01E02.mp4
    ├── A S01E03.mp4
    ├── A S01E04.mp4
    ├── other_none_video_files.ext
    └── other_folder
        ├── other_video1.mp4
        ├── other_video2.mp4
        ├── other_video3.mp4
        └── other_video4.mp4
```

Anime Subtitle Renamer对字幕文件的读取会遍历路径内所有字幕文件，可以读取的字幕所在目录需满足以下要求：

- 字幕所在目录和子文件夹中均不允许存在其他字幕文件
- 字幕文件有集数标识，如`孤独摇滚！ - S01E01 - 孤独的转机.ass`或`[DMG&VCB-Studio] BOCCHI THE ROCK! [06][Ma10p_1080p][x265_flac].srt`
- 示例字幕所在目录结构如下：

```file
    sub_src_dir
    │   ├── tc
    │   │   ├── A[01].tc.ass
    │   │   ├── A[02].tc.ass
    │   │   ├── A[03].tc.ass
    │   │   └── A[04].tc.ass
    │   └── sc
    │       ├── A[01].sc.ass
    │       ├── A[02].sc.ass
    │       ├── A[03].sc.ass
    │       └── A[04].sc.ass
```

若将字幕目标目录设置与视频文件所在目录一致，则输出示例应为：

```file
    video_dir(sub_src_dir)
    ├── A S01E01.mp4
    ├── A S01E02.mp4
    ├── A S01E03.mp4
    ├── A S01E04.mp4
    ├── A S01E01.custom_language_ext1.ass
    ├── A S01E02.custom_language_ext1.ass
    ├── A S01E03.custom_language_ext1.ass
    ├── A S01E04.custom_language_ext1.ass
    ├── A S01E01.custom_language_ext2.ass
    ├── A S01E02.custom_language_ext2.ass
    ├── A S01E03.custom_language_ext2.ass
    ├── A S01E04.custom_language_ext2.ass
    ├── other_none_video_files.ext
    └── other_folder
        ├── other_video1.mp4
        ├── other_video2.mp4
        ├── other_video3.mp4
        └── other_video4.mp4
```

## 使用流程

1. 调整视频所在目录、字幕所在目录文件结构，见[视频和字幕文件目录说明](#视频和字幕文件目录说明)
2. 按照实际情况修改基本配置中的视频所在目录、字幕所在目录、字幕目标目录（视频所在目录和相同则可以实现播放器中字幕自动识别）
3. 选取匹配模式（`ai`、`raw`、`ab`），若选择`ai`，则需要配置大模型服务商的`Base URL`、`API Key`和`Model Name`；若选择`raw`，则需要配置匹配位置和匹配正则
4. 设置是否清除原文件为False、Debug模式为True，运行程序，弹出窗口预览当前配置下字幕文件重命名的预计结果

<p align="center">
    <img title="RenamingPreview" src="docs/preview/renaming_preview.png" alt="" width=50%>
</p>

5. 确认重命名无误，设置是否清除原文件为True、Debug模式为False，运行程序，完成重命名字幕文件的生成

## 配置说明

### 基本配置

- 匹配模式（match_method）：可选ab、raw、 ai
- 是否清除原文件（clear_files）：如果是True，则在生成新字幕文件前删除字幕目标目录下所有字幕文件
- Debug模式（debug_mode）：如果是True，则不会生成新字幕文件，而是弹窗显示当前配置下字幕文件重命名的预计结果
- 视频所在目录（video_dir）
- 字幕所在目录（sub_src_dir）
- 字幕目标目录（sub_tar_dir）：设置为与视频所在目录相同，则实现Jellyfin（或其他播放器）对外部字幕文件的自动读取；暂不支持设定为与字幕所在目录相同

### 高级配置

- 匹配视频格式（video_ext）：python列表格式，默认为`['mp4', 'mkv']`，确定哪些后缀的文件将被视为视频
- 匹配字幕格式（subtitle_ext）：python列表格式，默认为`['ass', 'srt']`，确定哪些后缀的文件将被视为字幕
- 视频集数位置（video_match_pos）：仅在`raw`模式下有效，输入应为大于等于-1的整数，用于确定匹配视频文件集数在文件名中对应的位置（可能存在匹配出多个数字的情况），默认为-1，即匹配出的最后一个数字，0表示匹配出的第一个数字，1表示匹配出的第二个数字，以此类推，一般选择0或-1即可
- 视频匹配正则（video_pattern）：仅在`raw`模式下有效，输入应为字符串形式正则表达式，用于匹配视频文件名中的集数信息，默认为`(?:[A-Za-z]{1,2})?\b\d{1,2}\b`
- 字幕集数位置（sub_match_pos）：仅在`raw`模式下有效，输入应为大于等于-1的整数，用于确定匹配字幕文件集数在文件名中对应的位置（可能存在匹配出多个数字的情况），默认为-1，即匹配出的最后一个数字，0表示匹配出的第一个数字，1表示匹配出的第二个数字，以此类推，一般选择0或-1即可
- 字幕匹配正则（sub_pattern）：仅在`raw`模式下有效，输入应为字符串形式正则表达式，用于匹配字幕文件名中的集数信息，默认为`(?:[A-Za-z]{1,2})?\b\d{1,2}\b`

### AI配置

- Base URL（base_url）：大模型服务商的`Base URL`，如`https://api.openai.com/v1`，具体详见您所使用的大模型服务商官网
- API Key（api_key）：大模型服务商的`API Key`，如`sk-xxxxxxxxxxxxxxxxxxxxxxxxx`，具体详见您所使用的大模型服务商官网
- Model Name（model）：选择使用的`Model Name`，如`gpt-3.5-turbo`，具体详见您所使用的大模型服务商官网

### 隐藏配置

- language_ext：原字幕语言后缀与自定义字幕语言后缀映射，json格式，用于生成新字幕语言名，如`tc`和`sc`将被转换为`繁體中文.chi`和`简体中文.chi`，默认为：

```json
{
    "chs": "简体中文.chi",
    "cht": "繁體中文.chi",
    "dm-chs": "简体中文.chi",
    "dm-cht": "繁體中文.chi",
    "tc": "繁體中文.chi",
    "sc": "简体中文.chi",
    "jptc": "繁日字幕.chi",
    "jpsc": "简日字幕.chi"
}
```

## 匹配模式介绍

### ab模式

- 默认的匹配模式
- 使用[AutoBangumi](https://github.com/EstrellaXD/Auto_Bangumi)中[raw_parser.py](https://github.com/EstrellaXD/Auto_Bangumi/blob/main/backend/src/module/parser/analyser/raw_parser.py)的正则表达式匹配视频和字幕文件中的集数信息

### raw模式

- 使用自定义的正则表达式匹配字幕文件中的集数信息
- 一般工作流程为：使用pattern提取视频/字幕文件中候选的数字信息，再使用match_pos选择提取出正确集数信息的位置

### ai模式（推荐）

- 更智能、泛用性更强的匹配模式
- 使用大模型自动识别视频和字幕文件中的集数信息，实现文件匹配
- 使用经验：Qwen2.5-32B-Instruct可稳定完成正确匹配，14B、7B模型可能存在个别文件匹配失败的情况
