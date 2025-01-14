# from PIL import Image
# import pytesseract
# import os

# # Update this path if you're on Windows
# # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# def image_to_text(image_path):
#     """
#     Convert an image to text using Tesseract OCR.
#     :param image_path: Path to the image file.
#     :return: Extracted text as a string.
#     """
#     try:
#         # Open the image file
#         img = Image.open(image_path)

#         # Perform OCR
#         text = pytesseract.image_to_string(img)

#         return text
#     except Exception as e:
#         return f"Error: {e}"

# def batch_process_images(directory):
#     """
#     Process all images in a directory and extract text.
#     :param directory: Path to the directory containing images.
#     :return: Dictionary with filenames as keys and extracted text as values.
#     """
#     results = {}
#     for filename in os.listdir(directory):
#         if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
#             file_path = os.path.join(directory, filename)
#             text = image_to_text(file_path)
#             results[filename] = text
#     return results

# if __name__ == "__main__":
#     # Example: Process a single image
#     image_path = "ss.png"
#     extracted_text = image_to_text(image_path)
#     print("Extracted Text from Image:")
#     print(extracted_text)

#     # # Example: Process a directory of images
#     # directory_path = "path/to/your/image_folder"
#     # results = batch_process_images(directory_path)

#     # print("\nBatch Processing Results:")
#     # for file, text in results.items():
#     #     print(f"File: {file}\nText: {text}\n")


# import easyocr

# # Initialize the reader
# reader = easyocr.Reader(['en'])

# # Perform OCR on an image
# text = reader.readtext('pp1.jpg', detail=0)
# print("Extracted Text:", text)

# print(type(text))

# screen_stuff= "\n\n"
# for t in text:
#     screen_stuff += str(t) + '\n'
    
# screen_stuff += "\n\n"


# with open("ss.txt", "a+") as f:
#     f.write(screen_stuff)






from PIL import Image 
from pytesseract import pytesseract 

# Defining paths to tesseract.exe 
# and the image we would be using 
path_to_tesseract = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
image_path = r'pp1.jpg'

# Opening the image & storing it in an image object 
img = Image.open(image_path) 

# Providing the tesseract executable 
# location to pytesseract library 
pytesseract.tesseract_cmd = path_to_tesseract 

# Passing the image object to image_to_string() function 
# This function will extract the text from the image 
text = pytesseract.image_to_string(img) 

# Displaying the extracted text 
print(text)


with open("ss.txt", "a+") as f:
    f.write(text)