# NSS Golf Perfect Shots Library

Welcome to the NSS Golf Perfect Shots Library project! This is an open-source web application that allows users to view and share stunning golf-related images. Users can view the images in an appealing card format, and admins can delete images from the gallery. Every image can be clicked to view in larger size and contains associated vidoo links for further content. Admins have the ability to delete images if necessary.

## Project Structure

The project is a Flask application with the following structure:

```
/NSSGolf
    /static
      /CSS
        main.css
      /images
    /templates
        admin.html
        index.html
        layout.html
        login.html
        register.html
        search.html
        pload.html
    __init__.py
    forms.py
    views.py
    models.py
    routes.py
README.md
requirements.txt
run.py
```

## Usage Instructions

1. **Visit the Site:** Go to nssgolfshots.com in your web browser.
2. **Register/Log In:** If you're a new user, register an account. If you're a returning user you should be logged in automatically.
3. **Browse the Gallery:** The gallery page is where you can see all the images uploaded to the site.
Click on an image to view it in a larger size. Each video has its associated video link (YouTube, Vimeo, etc.).
4. **Uploading an Image:** If you are logged in, you can upload your own images. Each image requires a link to a video to verify the shot is as shown in the image.
    The image must show the swing of the shot and what the minimap looked like. When performing a swing, the game hides the minimap. You must edit the photo to include the minimap in the image.
    You will be asked to input the stats of the shot such as Wind Speed, Flag Position, etc. Answer correctly, otherwise the image will not be accepted.
    After submitting your image, an Admin will review the submission and either accept or deny it.
5. **Delete an Image (Admins Only):** If you're an admin, you can click the delete icon at the bottom of an image to remove it from the gallery. You'll be asked to confirm this action since it's irreversible.

## Contribution Guidelines

If you'd like to contribute to this project, you're more than welcome! Please follow these steps:

1. **Fork the Repository:** Click the 'Fork' button at the top-right of this page to create a copy of this repository on your GitHub account.
2. **Clone the Repository:** Clone the repository to your local machine.
3. **Create a Branch:** Create a new branch to contain your changes.
4. **Install dependencies:** A requirements.txt file is provided, if you use pip, you can type ```pip install -r requirements.txt``` in the console.
5. **Make Your Changes:** Update, fix, or add new features to the project.
6. **Test Your Changes:** Make sure your changes are working correctly and don't introduce new bugs.
7. **Push Your Changes:** Push your changes to your GitHub repository.
8. **Submit a Pull Request:** From your repository, click 'New pull request' and submit it.

Please ensure your code is clean, well-commented, and well tested.

## Additional Information

This project is built with Flask, a lightweight WSGI web application framework. It's designed to make getting started quick and easy, with the ability to scale up to complex applications.
https://flask.palletsprojects.com/en/2.3.x/

If you need further information or have any questions, please feel free to open an issue on this repository.

Thank you for your interest in our NSS Golf Perfect Shots Library project! We look forward to your contribution.
