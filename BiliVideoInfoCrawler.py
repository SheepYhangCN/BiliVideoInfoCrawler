import requests
import re
import json
import os
import ffmpeg
import asyncio
from bilibili_api import video
import time
import urllib

def av2bv(aid):
	return json.loads(requests.get("https://api.bilibili.com/x/web-interface/view?aid="+str(aid),headers = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edge/91.0.864.67"
			}).content)["data"]["bvid"]

async def Crawl(id, filename = ""):
	id = str(id)
	filename = str(filename)
	if (id.lower().startswith("https://") or id.lower().startswith("http://") or id.lower().startswith("www.")):
		url = id
		if (url.endswith("/")):
			url = url.rstrip("/")
		id = url.split("/")[-1]
	else:
		if (not (id.lower().startswith("av") or id.lower().startswith("bv"))):
			if (id.isdigit()):
				id = "av"+id
			else:
				id = "BV"+id
		url = "https://www.bilibili.com/video/"+id
	head = {
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edge/91.0.864.67",
				"Referer":url
			}
	resp = requests.get(url, headers=head)

	if (filename == ""):
		filename = id

	print("文件名：",filename)
	if (id.lower().startswith("av")):
		#v = video.Video(aid = int(id.lstrip("av"))) #等待bilibili-api-python修复bvid转换算法后更换
		v = video.Video(bvid = av2bv(int(id.lstrip("av"))))
	elif (id.lower().startswith("bv")):
		v = video.Video(bvid = id)
	info = await v.get_info()
	with open(filename+".json", mode="w", encoding="utf-8") as f:
		f.write(json.dumps(info, indent = 4, ensure_ascii = False))
	with open(filename+".txt", mode="w", encoding="utf-8") as f:
		f.write(id)
		f.write("\n标题:"+info["title"])
		f.write("\n播放量："+str(info["stat"]["view"]))
		f.write("\n投稿时间："+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(info["pubdate"])))
		f.write("\n点赞: "+str(info["stat"]["like"]))
		f.write("\n投币: "+str(info["stat"]["coin"]))
		f.write("\n收藏: "+str(info["stat"]["favorite"]))
		f.write("\n分享: "+str(info["stat"]["share"]))
		f.write("\n类型："+("原创" if info["copyright"] == 1 else "转载"))
		f.write("\n投稿者: ")
		if ("staff" in info):
			staffs = ""
			for i in info["staff"]:
				staffs = staffs + i["name"]+"、"
			f.write(staffs.rstrip("、"))
		else:
			f.write(info["owner"]["name"])
	print("数据存储完成")

	pic_url = info["pic"]
	pic_data = urllib.request.urlopen(pic_url).read()
	with open(filename+"."+pic_url.split(".")[-1], mode="wb") as f:
		f.write(pic_data)
	print("封面下载完成")

	json_data = re.findall("<script>window.__playinfo__=(.*?)</script>", resp.text)[0]
	json_data = json.loads(json_data)

	audio_url = json_data["data"]["dash"]["audio"][0]["backupUrl"][0]
	audio_data = requests.get(audio_url,headers=head)
	with open(filename+".a.mp3", mode="wb") as f:
		f.write(audio_data.content)
	print("音频下载完成")

	video_url = json_data["data"]["dash"]["video"][0]["backupUrl"][0]
	video_data = requests.get(video_url,headers=head)
	with open(filename+".v.mp4", mode="wb") as f:
		f.write(video_data.content)
	print("视频下载完成")

	v = ffmpeg.input(filename+".v.mp4")
	a = ffmpeg.input(filename+".a.mp3")
	out = ffmpeg.overwrite_output(ffmpeg.output(v,a,filename+".mp4"))
	ffmpeg.run(out)
	print("视频合并完成")

	os.remove(filename+".v.mp4")
	os.remove(filename+".a.mp3")
	print("临时文件已删除")

if (__name__ == "__main__"):
	asyncio.run(Crawl(input("输入该视频的av/BV号或链接："),input("自定义文件名（留空使用av/BV号）：")))