

# 🧠 AI-Powered Feature Engineering Suite  


This project provides a comprehensive suite of tools for exploratory data analysis (EDA) and feature engineering. It leverages cutting-edge AI models to generate insightful feature suggestions, enabling data scientists and engineers to streamline their workflows and improve model performance. The suite includes tools for generating detailed EDA summaries and AI-powered feature suggestions, making it an essential resource for any data-driven project.

---

## 🚀 Features

- **Exploratory Data Analysis (EDA):**  
  - Generates detailed summaries of datasets, including column statistics and target identification.  
  - Provides insights into data distribution, missing values, and key metrics for numeric columns.  

- **AI-Powered Feature Suggestions:**  
  - Uses Google's Gemini Generative AI to generate context-aware feature suggestions.  
  - Supports domain-specific prompts for tailored feature engineering.  

- **Integration-Ready:**  
  - Designed to integrate seamlessly with data pipelines and machine learning workflows.  
  - Outputs feature suggestions in JSON format for easy consumption by downstream processes.  

---

## 🛠️ Tech Stack

- **Frontend:**  
  - `Streamlit`: For building the user interface.  
  - `Pandas`: For data manipulation and display.  
  - `Requests`: For API communication.  

- **Backend:**  
  - `FastAPI`: For creating RESTful APIs.  
  - `Pandas`: For data analysis and processing.  
  - `Feature Engine`: For EDA and feature suggestions.  

- **AI/ML:**  
  - `Google Generative AI (Gemini)`: For generating feature suggestions.  
  - `Sentence Transformers`: For text embedding and similarity search.  
  - `FAISS`: For efficient similarity search in high-dimensional spaces.  

- **Utilities:**  
  - `Dotenv`: For environment variable management.  
  - `Json`: For parsing and handling JSON data.  

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher  
- pip for package management  
- Google Cloud API key for Gemini Generative AI  

### Installation Steps

1. Clone the repository:  
   ```bash
   git clone [your-repository-url]
   cd [repository-name]
   ```

2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:  
   - Create a `.env` file and add your Google Cloud API key:  
     ```bash
     echo "GOOGLE_API_KEY=your-api-key" > .env
     ```

4. Start the backend server:  
   ```bash
   uvicorn backend.main:app --reload
   ```

5. Launch the frontend:  
   ```bash
   streamlit run frontend/app.py
   ```

---

## 💻 Usage

### Running the Application

1. **Start the Backend:**  
   ```bash
   uvicorn backend.main:app --reload
   ```
   - The backend server will start on `http://localhost:8000`.

2. **Launch the Frontend:**  
   ```bash
   streamlit run frontend/app.py
   ```
   - The frontend will open in your default browser at `http://localhost:8501`.

### Using the Application

1. **Upload a CSV File:**  
   - Navigate to the frontend interface.  
   - Click the file uploader and select a CSV file.  

2. **Generate EDA Summary:**  
   - Click the "Upload" button to generate and display the EDA summary.  

3. **Get Feature Suggestions:**  
   - Click the "Get Feature Suggestions" button to fetch and display AI-generated feature ideas.  

---

## 📂 Project Structure

```markdown
.
├── backend/
│   ├── main.py
│   ├── rag_engine.py
│   ├── prompts.py
│   └── feature_engine.py
├── frontend/
│   └── app.py
├── requirements.txt
└── .env
```

---

## 📸 Screenshots

**[Screenshot of the frontend interface with EDA summary and feature suggestions]**

---

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to this project, please fork the repository and submit a pull request. Ensure your changes are well-documented and follow the project's coding standards.

---

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## 📬 Contact

For questions, suggestions, or feedback, please contact the maintainers at [your-email@example.com](mailto:your-email@example.com).

---

## 💖 Thanks Message

A heartfelt thank you to all contributors and users who have supported this project. Special thanks to Google for their Generative AI capabilities, which power the feature suggestion engine.

---

This README was generated with ❤️ by readme.ai.
