import image_poc as poc
import time

input_folder = "D:\\Users\\ejose\\Documents\\Github\\NSDSYST\\test_images"
brightness = [50,20,10,5]
contrast = [50,20,10,5]
sharpness = [0,1,10,100]

filenames = poc.getFilenames(input_folder)
output_folder = poc.createFolder(input_folder)

for i in range(len(brightness)):
    print("Running Params:", brightness[i], contrast[i], sharpness[i], "...")
    start = time.time()
    poc.coordinator(input_folder, filenames, output_folder, brightness[i], contrast[i], sharpness[i])
    end = time.time()-start
    print(f"Total Run: {end:.4f}s ({end/len(filenames):.4f}s per image)")
    print("")

exit(0)