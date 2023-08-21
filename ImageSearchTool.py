#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image
import threading
import time
import sqlite3
import os
import sys
import torch
import numpy as np
import clip
import faiss
import hashlib
import subprocess

maxn=0
image_index = 0
device = "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
directory=''

def get_ocr_result(filepath):
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	tesseract_isolated_path = os.path.join(base_path, 'tesseract_isolated.py')
	command = ["python", tesseract_isolated_path]
	process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	output_data, error_data = process.communicate(filepath)
	if process.returncode != 0:
		print(f"An error occurred: {error_data}")
		return None
	else:
		return output_data[:1000000]

def generate_id(input_string):
	sha256 = hashlib.sha256()
	sha256.update(input_string.encode('utf-8'))
	return int.from_bytes(sha256.digest()[:6], byteorder='big')

def on_search_clip():
	query = entry_search.get()
	global directory,maxn,images
	if query and directory:
		text = query
		text_tokenized = clip.tokenize([text]).to(device)
		with torch.no_grad():
			text_features = model.encode_text(text_tokenized)
		text_features_np = text_features.cpu().numpy()
		faiss_index_file = os.path.join(directory, 'faiss_index.idx')
		index = faiss.read_index(faiss_index_file)
		norms = np.linalg.norm(text_features_np, axis=1, keepdims=True)
		text_features_np /= norms
		maxn=100
		db_file = os.path.join(directory, 'image_names.db')
		D, I = index.search(text_features_np, 100)
		images=[]
		conn = sqlite3.connect(db_file)
		cursor = conn.cursor()
		for i, idx in enumerate(I[0]):
			image_id = idx
			cursor.execute('SELECT name FROM images WHERE id = ?', (str(image_id),))
			result = cursor.fetchone()
			if result:
				image_name = result[0]
				images.append(str(image_name))
				#print(f"Rank {i+1}: {image_name} (Distance: {D[0][i]})")
			else:
				print(f"Rank {i+1}: Image not found in database (ID: {image_id}, Distance: {D[0][i]})")
		conn.close()
		print(f"Images list: {images}")
		load_images2(images,directory=directory)
		
def on_search_img():
	global directory,maxn,images
	file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")])
	if file_path and directory:
		image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)
		with torch.no_grad():
			image_features = model.encode_image(image)
		image_features_np = image_features.cpu().numpy()
		norms = np.linalg.norm(image_features_np, axis=1, keepdims=True)
		image_features_np /= norms
		faiss_index_file = os.path.join(directory, 'faiss_index.idx')
		db_file = os.path.join(directory, 'image_names.db')
		conn = sqlite3.connect(db_file)
		cursor = conn.cursor()
		maxn=100
		index = faiss.read_index(faiss_index_file)
		images=[]
		D, I = index.search(image_features_np, 100)
		for i, idx in enumerate(I[0]):
			image_id = idx
			cursor.execute('SELECT name FROM images WHERE id = ?', (str(image_id),))
			result = cursor.fetchone()
			if result:
				image_name = result[0]
				images.append(str(image_name))
				print(f"Rank {i+1}: {image_name} (Distance: {D[0][i]})")
			else:
				print(f"Rank {i+1}: Image not found in database (ID: {image_id}, Distance: {D[0][i]})")
		conn.close()
		load_images2(images,directory=directory)

def clipcallbck(cur,tot,start_time):
	progress_bar['value'] = (cur/tot)*100
	elapsed_time = time.time() - start_time
	remaining_time = elapsed_time * (tot - cur) / cur
	label_status.config(text=f"Progress: {cur}/{tot} - ETA {int(remaining_time)} s")

def clip_vec(progress_callback=clipcallbck):
	button_update_cl.config(state=tk.DISABLED)
	image_folder = directory
	faiss_index_file_path = directory
	faiss_index_file = os.path.join(faiss_index_file_path, 'faiss_index.idx')
	db_file = os.path.join(faiss_index_file_path, 'image_names.db')
	dimension = 512
	index_flat = faiss.IndexFlatL2(dimension)
	index = faiss.IndexIDMap(index_flat)
	conn = sqlite3.connect(db_file)
	cursor = conn.cursor()
	cursor.execute('''CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY, name TEXT)''')
	conn.commit()
	if os.path.exists(faiss_index_file):
		index = faiss.read_index(faiss_index_file)
	image_paths = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
	existing_ids = set(row[0] for row in cursor.execute('SELECT id FROM images'))
	new_image_paths = []
	for image_path in image_paths:
		image_name = os.path.basename(image_path)
		image_id = generate_id(image_name)
		if image_id not in existing_ids:
			new_image_paths.append(image_path)
	totaltoclip=len(new_image_paths)
	srt=time.time()
	clipped=0
	clr=0
	text_log.insert(tk.END, 'Found '+str(len(existing_ids))+' existing images.' + '\n')
	text_log.insert(tk.END, 'Found '+str(len(new_image_paths))+' new images for CLIP vectorize.' + '\n')
	for image_path in new_image_paths:
		clipped=clipped+1
		clr=clr+1
		try:
			image_name = os.path.basename(image_path)
			image_id = generate_id(image_name)
			image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
			with torch.no_grad():
				image_features = model.encode_image(image)
			image_features_np = image_features.cpu().numpy()
			norms = np.linalg.norm(image_features_np, axis=1, keepdims=True)
			image_features_np /= norms
			index.add_with_ids(image_features_np, np.array([image_id])) 
			cursor.execute('INSERT INTO images (id, name) VALUES (?, ?)', (image_id, image_name))
			progress_callback(clipped,totaltoclip,srt)
		except Exception as e:
			print(f"An error occurred while processing the image {image_path}: {str(e)}")
		if clr>=133:
			conn.commit()
			faiss.write_index(index, faiss_index_file)
			clr=0
	conn.commit()
	faiss.write_index(index, faiss_index_file)
	button_update_cl.config(state=tk.NORMAL)
	text_log.insert(tk.END, 'CLIP finished.' + '\n')
	
def clip_vic():
	if directory:
		threading.Thread(target=clip_vec).start()


def initialize_db(db_path):
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS main (
			name TEXT,
			text TEXT,
			label1 TEXT,
			label2 TEXT,
			label3 TEXT
		)
	''')
	conn.commit()
	return conn, cursor


def update_database(image_directory, conn, cursor, progress_callback=None, log_callback=None):
	existing_images = set()
	cursor.execute('SELECT name FROM main')
	for row in cursor.fetchall():
		existing_images.add(row[0])
	supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
	images_to_ocr = [filename for filename in os.listdir(image_directory)
					if filename.endswith(supported_extensions) and filename not in existing_images]
	total_images = len(images_to_ocr)
	if log_callback:
		log_callback(f'Found {len(existing_images)} existing images.')
		log_callback(f'Found {total_images} new images for OCR.')
	for i, filename in enumerate(images_to_ocr):
		filepath = os.path.join(image_directory, filename)
		text = get_ocr_result(filepath)  # SQLite的限制, 最多1000000字符
		cursor.execute('INSERT INTO main (name, text, label1, label2, label3) VALUES (?, ?, ?, ?, ?)', (filename, text, None, None, None))
		conn.commit()
		if progress_callback:
			percentage = (i + 1) / total_images * 100
			progress_callback(percentage, i + 1, total_images)
	if log_callback:
		log_callback('Database updated successfully.')
	
def create_or_update_database(image_directory, progress_callback=None, log_callback=None):
	db_path = os.path.join(image_directory, 'IMGSearch.db')
	conn, cursor = initialize_db(db_path)
	update_database(image_directory, conn, cursor, progress_callback, log_callback)
	conn.close()
	button_update.config(state=tk.NORMAL)
	
def search_images(query, image_directory):
	global maxn
	db_path = os.path.join(image_directory, 'IMGSearch.db')
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute("SELECT name FROM main WHERE LOWER(text) LIKE LOWER(?) LIMIT 100", ('%' + query + '%',))
	results = cursor.fetchall()
	conn.close()
	maxn=0
	if results:
		text_log.insert(tk.END, 'Matching images:' + '\n')
		for row in results:
			text_log.insert(tk.END,row[0])
			maxn=maxn+1
	else:
		text_log.insert(tk.END,'No matching images found.')
	return results

def on_create_update():
	global directory
	if directory:
		start_time = time.time()
		def progress_callback(percentage, current, total):
			progress_bar['value'] = percentage
			elapsed_time = time.time() - start_time
			remaining_time = elapsed_time * (total - current) / current
			label_status.config(text=f"Progress: {current}/{total} - ETA {int(remaining_time)} s")
		def log_callback(message):
			text_log.insert(tk.END, message + '\n')
		button_update.config(state=tk.DISABLED)
		threading.Thread(target=create_or_update_database, args=(directory, progress_callback, log_callback)).start()
		
def on_search():
	query = entry_search.get()
	global directory
	if query and directory:
		images = search_images(query, directory)
		load_images(images,directory=directory)
		
def load_images(image_names, directory):
	global image_index, images
	image_index = 0
	images = [os.path.join(directory, name[0]) for name in image_names]
	if images:
		load_image()
		
def load_images2(image_names, directory):
	global image_index, images
	image_index = 0
	images = [os.path.join(directory, name) for name in image_names]
	if images:
		load_image()
		
def load_image():
	global maxn,image_index
	image_index=image_index%maxn
	if images:
		img = Image.open(images[image_index])
		w, h = img.size
		ratio = min(430/w, 300/h) 
		new_size = (int(w*ratio), int(h*ratio))
		img = img.resize(new_size, Image.Resampling.LANCZOS)
		img = ImageTk.PhotoImage(img)
		label_image.config(image=img)
		label_image.image = img
		filename = os.path.basename(images[image_index])
		label_n.config(text=filename)
		
def on_previous():
	global image_index
	if images and image_index > 0:
		image_index -= 1
		load_image()
		
def on_next():
	global image_index
	if images and image_index < len(images) - 1:
		image_index += 1
		load_image()
		
def setdir():
	global directory
	directory=filedialog.askdirectory()
	root.title("Image Search Tool-"+directory)
		
root = tk.Tk()
root.geometry('800x400')
root.title("Image Search Tool")

canvas = tk.Canvas(root, width=1, height=400, bg='black')
canvas.place(x=262, y=0)


button_browse = ttk.Button(root, text="Browse..", command=setdir)
button_browse.place(x=10, y=10)

button_update = ttk.Button(root, text="OCR", command=on_create_update)
button_update.place(x=150, y=10)

button_update_cl = ttk.Button(root, text="CLIP Vectorize", command=clip_vic)
button_update_cl.place(x=120, y=40)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=237, mode="determinate")
progress_bar.place(x=10, y=120)

label_status = ttk.Label(root, text="No current progress...")
label_status.place(x=10, y=98)

text_log = tk.Text(root, width=32, height=19)
text_log.place(x=10, y=136)

entry_search = ttk.Entry(root, width=15)
entry_search.place(x=285, y=10)

button_search = ttk.Button(root, text="Search", command=on_search)
button_search.place(x=440, y=10)

button_search_clip = ttk.Button(root, text="Search(CLIP)", command=on_search_clip)
button_search_clip.place(x=540, y=10)

button_search_img = ttk.Button(root, text="Search(IMG)", command=on_search_img)
button_search_img.place(x=670, y=10)

button_previous = ttk.Button(root, text="Previous", command=on_previous)
button_previous.place(x=300, y=360)

label_n = ttk.Label(root, text="Image Preview..")
label_n.place(x=400, y=365)

label_image = ttk.Label(root)
label_image.place(x=315, y=50)

button_next = ttk.Button(root, text="Next", command=on_next)
button_next.place(x=670, y=360)

images = []
image_index = 0

root.mainloop()