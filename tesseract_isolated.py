#!/usr/bin/env python3

import sys
import pytesseract
from PIL import Image

def main():
	filepath = sys.stdin.readline().strip()
	image = Image.open(filepath)
	text = pytesseract.image_to_string(image, lang='chi_sim+eng+jpn')
	print(text)
	
if __name__ == "__main__":
	main()
	