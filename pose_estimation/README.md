# pose_estimation
Code to create random poses as Trainingsdata, Training a CNN to estimate Joint rotations and final implementation

This code was written with Python 3.11.5 and was executed in Maya 2025 and 2026

In order to use the code replace the placeholder paths in const.py with the desired locations and change the training_data_path placeholder in data_generation.py
Additionally you will need to change the draw_to_image_folder path in the maya_deployment module.

To install the necessary dependencies use: pip install -r requirements.txt

In order to create Trainingsdata, choose the amount of images you want by using the playback range in Maya and launch the pose_generation module via the script editor. 
This will create images and corresponding labels.
When this is done, execute the data_prep module to seperate the data into training, validation and test data.
In order to create and train the CNN execute the CNN_training module.
To use the result, ececute the pose_server module and launch the maya_deployment script via the maya script editor

As an alternative you can add the userSetup.py module into C:\Users\Documents\maya\2026\scripts in order to create a shelf inside maya. You will need to change the tool_dir path to the location of the repository and site_packages_dir to the location of the installed dependencies.

Enjoy!



Additional modules such as use_model, screenshot, crop_images, analyze and difference_of_silhouettes are legacy code used to evaluate results and to help with writing my thesis. They are not up to date and contain unnecessary code and I will most likely not update them (Just ignore them, they are not that interesting)