# Image_Search_Tool
对本地图库实现搜索内容/文字/以图搜图，并含有其他扩展<br>
Implementing search content/text/image search within the local photo gallery, along with other extensions.

## 效果
1.输入文字搜索内容(默认输出最多100张,按匹配度从前往后排序)/Search content by entering text(output 100 images max by default, sorted by relevance)<br><img width="912" alt="Screenshot 2023-08-18 at 09 20 13" src="https://github.com/sszzz830/Image_Search_Tool/assets/32834442/e7c9358e-5f7d-4d64-b5e8-472e5d73dc48"><br>

2.输入文字搜索精确包含指定文字在图上的图片/Search for images that precisely contain the specified text<br><img width="912" alt="Screenshot 2023-08-18 at 09 24 19" src="https://github.com/sszzz830/Image_Search_Tool/assets/32834442/53d506a8-bdea-4f9f-a991-6a9c8b7405c5"><br>

3.输入图片搜索相似图片/Search for similar images by inputting an image(演示输入也是一张猫猫虫/demo image input is a Bugcat Capoo)<br><img width="912" alt="Screenshot 2023-08-18 at 09 23 48" src="https://github.com/sszzz830/Image_Search_Tool/assets/32834442/65640d33-de18-4b8b-a998-c95ccc8b0d37">

## 使用方法
0.安装依赖.运行InstallRequirements.bat安装req.txt内的依赖.建议python版本3.9.此外,还要安装tesseract,并在系统PATH内添加tesseract.exe位置或者在tesseract_isolated.py内import pytesseract后加入pytesseract.pytesseract.tesseract_cmd='',''内指定tesseract二进制文件的位置.<br>
1.使用Browse按钮选择目标文件夹<br>
2.若该文件夹未执行过ocr和CLIP向量化,则需要点击ocr按钮和CLIP Vectorize按钮,对指定文件夹内图片执行向量化和ocr构建数据库.<br>
3.在输入框输入搜索内容即可输入文字搜索内容和输入文字搜索精确包含指定文字在图上的图片,点击Search(IMG)即可选择图片然后以图搜图.<br>
0.Install dependencies. Run InstallRequirements.bat to install the dependencies listed in req.txt. Python 3.9 is recommended. In addition, you will need to install Tesseract and add the location of tesseract.exe to the system PATH, or specify the location of the Tesseract binary file in tesseract_isolated.py by adding pytesseract.pytesseract.tesseract_cmd = '','' is the location of tesseract.exe.<br>
1.Use the Browse button to select the target folder<br>
2.If the folder has not been processed with OCR and CLIP vectorization, you will need to click the OCR button and the CLIP Vectorize button to vectorize and OCR the images within the specified folder, building a database.<br>
3.Enter the search content in the input box to search for content and images that precisely contain the specified text. Click Search(IMG) to select an image and then search by image.<br>

## 实现方法
使用tesseract作为ocr引擎,使用OpenAI的CLIP模型对文字和图片向量化.构建索引时会在图片文件夹路径下生成两个SQLite3数据库和一个FAISS Index,分别保存图片的ocr文本-名称,名称-ID和FAISS索引.精确查询文本时,会从ocr数据库中查找包含输入(大小写不敏感)的图片名称;当查询图片内容时,会对输入文本使用CLIP向量化,然后从FAISS向量数据库找出最匹配的向量对应的图片名称;当以图搜图时,会对输入图片向量化,然后从FAISS向量数据库找出最匹配的向量对应的图片名称.<br>
Utilizes Tesseract as the OCR engine and OpenAI's CLIP model to vectorize both text and images. During index construction, two SQLite3 databases and one FAISS Index will be created under the image folder path, saving the images' OCR text-names, names-IDs, and FAISS indices. When querying text precisely, the image names containing the input (case-insensitive) will be searched in the OCR database; when querying image content, the input text will be vectorized using CLIP, and the most matching vector's corresponding image name will be found in the FAISS vector database; when searching by image, the input image will be vectorized, and the most matching vector's corresponding image name will be found in the FAISS vector database.<br>


## 扩展/Extension
0.改bug,提升性能,多线程ocr,支持gpu加速等等(开发中)<br>
1.使用go-cqhttp实时保存所有群聊图片并且加载进数据库方便日后搜图的组件(开发中)<br>
2.使用flask开发的api(计划开发)<br>
3.网页版(计划开发)<br>
4.其他<br>
0.Fix bugs, improve performance, multi-threaded OCR, support for GPU acceleration, etc. (in development) <br>
1.A component that uses go-cqhttp to save all group chat images in real time and load them into the database for convenient future image searches (in development) <br>
2.An API developed with Flask (planned development) <br>
3.Web version (planned development) <br>
4.more...<br>
