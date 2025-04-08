# Genesys Cloud - Get User Time 😎

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## Overview

**Genesys Cloud Get User Time** is a desktop application built with Python and Tkinter that collects user time data from the Genesys Cloud API. The application provides a user-friendly interface where you can set a date range, input a list of user logins, and export the resulting data to a CSV file. You get real-time feedback via a progress bar, status messages, and a log area! 🚀

## Features

- **Intuitive GUI:**  
  Built using Tkinter with a grid layout for clean and organized widgets.
- **Input Validation:**  
  Ensures the end date is not earlier than the start date.
- **Progress Feedback:**  
  Displays a progress bar, status messages, and a scrolling log to show detailed process updates.
- **Multithreading:**  
  Runs API calls in a separate thread to keep the interface responsive.
- **CSV Export:**  
  Exports the collected data into a CSV file for further analysis.
- **Secure Configuration:**  
  Uses a `.env` file for storing API credentials and configuration.

## Installation

### Prerequisites

- Python 3.7 or higher  
- pip (Python package installer)

### Steps

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/gstvbatista/gc_get_user_time.git
    cd gc_get_user_time
    ```

2. **Create and Activate a Virtual Environment:**

    ```bash
    python -m venv venv
    ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Configure the Environment:**

    Create a `.env` file in the project root (if not already present) with the following content, replacing the placeholders with your actual API credentials:

    ```ini
    ENVIRONMENT=mypurecloud.com
    CLIENT_ID=your_client_id
    CLIENT_SECRET=your_client_secret
    SSL_VERIFY=true
    ```

## Usage

1. **Run the Application:**

    ```bash
    python app.py
    ```

2. **Fill in the Fields:**
   - **Data Início:** Enter the start date (format **DD/MM/AAAA**).
   - **Data Final:** Enter the end date (format **DD/MM/AAAA**).  
     _Note: The end date must not be earlier than the start date._
   - **Lista de Usuários:** Enter one user login per line. Use the scrollbar if needed.

3. **Click on "Processar":**  
   The application will begin processing the data, showing a progress bar, status updates, and a detailed log of each step.

4. **Save the CSV File:**  
   Once the process is complete, you'll be prompted to choose where to save the CSV file with the collected data.

5. **Enjoy Your Data!** 📊

## Development

Contributions are welcome! If you want to improve the project or add new features, please fork the repository and submit a pull request or open an issue for discussion.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for the full license text. 📄

## Contact

For any questions or further inquiries, please open an issue on [GitHub](https://github.com/gstvbatista/gc_get_user_time) or contact the maintainer directly.

---

Enjoy using Genesys Cloud Get User Time and happy coding! 😊
