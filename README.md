### INSTRUCTIONS
To use this module you must have docker and docker-compose installed. Note both docker and docker-compose are installed by default with docker desktop. Once installed, run the first 2 commands in commands.txt are used to create the image. After install finishes use the 3rd command to run it locally or start the server with docker desktop. To access the image via the command line you can use the 4th command which will give you access to the django container or the 5th command for the mysql container (note the containers must be running for this to work. If you ran them in the terminal you will need to open up a separate terminal to access them). Finally, data from the mysql database will be stored on your local machine when the image is terminated.
To access the website created in django, use port 8000 on local host. Once again, this will only work if the image is active.

To get the books data, go [here](https://www.kaggle.com/datasets/mohamedbakhet/amazon-books-reviews/data?select=books_data.csv) and download just the books_data.csv file. Then place the file in the data folder.

To get the models for book reccomendations, go [here]() and download all files. Place them in the recommendation folder in library_project.

To add tables to the mysql database and populate them, simply use run the intialize_db.py file in the django container. Expect this to take approximately 8 minutes since this process includes the creation of embeddings for each book title in the database using the pretrained doc2vec model.

