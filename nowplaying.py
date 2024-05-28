import os
import time
import subprocess
import pybase64
from PIL import Image

image_path = '/Users/limit/live/歌曲/image.jpeg'  # 保存封面的位置
text_path = '/Users/limit/live/歌曲/play.txt'  # 保存媒体信息的位置
limit_numbers = [65, 30, 30]  # 你需要提供一个限制字符数量的值，第一项为歌曲名称，第二项为作者，第三项为专辑名
limit_get_image_number = 3  # 在封面获取失败后最多获取几次封面
refresh_rate = 1  # 间隔多久检测一次媒体变化，单位为秒，越小则越吃性能


# 获取当前播放媒体的标识码,只截取少量信息，方便之后判断优化性能
def get_artist_title_raw():
    result = subprocess.run(['nowplaying-cli', 'get', 'ContentItemIdentifier'], capture_output=True)
    return result


# 限制媒体信息字符数量的函数
def truncate_lines(limited_output_lines, limit_numbers):
    truncated_lines = []
    for i, line in enumerate(limited_output_lines):
        if i < len(limit_numbers):
            limit = limit_numbers[i]
            if len(line) > limit:
                truncated_lines.append(line[:limit] + "...")
            else:
                truncated_lines.append(line)
    return truncated_lines


# 获取当前艺术家和标题、专辑并作处理的函数
def get_artist_title():
    result = subprocess.run(['nowplaying-cli', 'get', 'title', 'artist', 'album'], capture_output=True)
    output = result.stdout.decode().strip()

    # 拆分输出为列表
    output_lines = output.split('\n')

    # 确保limited_output_lines至少有三个元素
    while len(output_lines) < 3:
        output_lines.append('')  # 添加空白项

    # 检测并限制每行字符数量
    limited_output_lines = truncate_lines(output_lines, limit_numbers)

    # 判断是否需要添加短横线和专辑信息
    # 判断是否有专辑这一项，没专辑且没作者的话直接输出标题，有作者的话输出标题+作者
    if not limited_output_lines[2]:
        if not limited_output_lines[1]:
            artist_title_album = limited_output_lines[0]
        else:
            artist_title_album = limited_output_lines[0] + "\n" + limited_output_lines[1]
    # 有专辑的话则判断专辑和标题是否一致，一致则不显示专辑
    else:
        if limited_output_lines[0] != limited_output_lines[2]:
            # 将艺术家和专辑连接在一行上，用短横线分隔
            artist_title_album = limited_output_lines[0] + "\n" + limited_output_lines[1] + " -『 " + \
                                 limited_output_lines[2] + " 』"
        else:
            artist_title_album = limited_output_lines[0] + "\n" + limited_output_lines[1]
    # 返回处理后的输出结果
    return artist_title_album


# 获取jpeg图像的base64数据的函数
def get_image_base64():
    result = subprocess.run(['nowplaying-cli', 'get', 'ArtworkData'], capture_output=True)
    return result.stdout.strip()


# 将base64图像数据保存到文件的函数
def save_image_from_base64(base64_data, file_path):
    with open(file_path, "wb") as f:
        f.write(pybase64.b64decode(base64_data))


# 获取文件大小
def check_image_size(filename):
    return os.path.getsize(filename)


# 主函数
def main():
    # 初始化变量
    previous_artist_title = ""
    task_count = 0

    while True:
        artist_title = str(get_artist_title_raw())
        # 检测当前播放媒体是否有变化，若有变化则进行任务，没有变化则在间隔之后，重新检测
        if artist_title != previous_artist_title:

            # 获取完整的媒体信息
            processed_artist_title = str(get_artist_title())
            # 媒体信息保存到文件中
            with open(text_path, 'w') as f:
                f.write(processed_artist_title)

            # 计数器
            count = 0

            # 获取并保存图像
            while True:
                # 获取图像的 base64 数据并保存为图片文件
                image_base64 = get_image_base64()
                save_image_from_base64(image_base64, image_path)

                # 检查图片文件大小
                image_size = check_image_size(image_path)

                # 判断是否小于100字节，小于的话再次获取
                if image_size < 100:
                    print("获取封面失败，尝试再次获取")
                    count += 1
                    time.sleep(0.5)
                    if count >= limit_get_image_number:
                        print("不再获取")
                        break
                    continue
                else:
                    break  # 图片大小大于等于100字节，跳出循环

            # 若获取图片成功的话，统一图片大小为200*200，
            # 注：Apple music能获得的封面为600*600，网易云能获得的为60*60，Spotify能获得的为150*150
            if count < limit_get_image_number:
                img = Image.open(image_path)
                img = img.resize((200, 200))
                img.save(image_path)

            previous_artist_title = artist_title

            print("\n当前正在播放\n", processed_artist_title, "\n")
            task_count += 1
            time.sleep(2)
        else:
            time.sleep(refresh_rate)


if __name__ == "__main__":
    main()
