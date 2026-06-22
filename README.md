

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
  - HTML5, Vanilla CSS (Glassmorphism & animated dark mode layout)
  - JavaScript (ES6+) for interactive UI logic and backend communication
  - Chart.js for data visualization (distributions & missing values)
  - Highlight.js for Python syntax highlighting

- **Backend:**  
  - `FastAPI`: For hosting RESTful APIs and serving the static frontend application.  
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
   git clone https://github.com/Divyansh-debug/AutoFeatureGenie.git
   cd AutoFeatureGenie
   ```

2. Install dependencies:  
   ```bash
   pip install -e .
   ```

3. Set up environment variables:  
   - Create a `.env` file and add your Google Cloud API key:  
     ```bash
     GEMINI_API_KEY=your-api-key
     ```

4. Start the server (hosts both backend and frontend):  
   ```bash
   uvicorn backend.main:app --reload
   ```

---

## 💻 Usage

### Running the Application

1. **Start the Backend and Frontend Server:**  
   ```bash
   uvicorn backend.main:app --reload
   ```
   - The application will be accessible in your browser at `http://localhost:8000`.

### Using the Application

1. **Upload a CSV File:**  
   - Navigate to the web application at `http://localhost:8000`.  
   - Drag and drop or browse to select a CSV file.  

2. **Generate EDA Summary:**  
   - Click "Analyse" to generate and display the interactive EDA summary, distributions, and column statistics.  

3. **Get Feature Suggestions:**  
   - Enter your target column (if any), switch to the "AI Features" tab, and click "Generate Features" to fetch and display AI-generated feature ideas.  

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
│   ├── index.html
│   ├── js/
│   │   └── app.js
│   └── css/
│       └── style.css
├── pyproject.toml
└── .env
```

---

## 📸 Screenshots

<img width="1919" height="1017" alt="Screenshot 2025-07-16 161716" src="https://github.com/user-attachments/assets/0d8d3d60-693a-463e-99b2-e7f8a2bc22dc" />
<img width="1919" height="1007" alt="Screenshot 2025-07-16 161735" src="https://github.com/user-attachments/assets/d0a97c95-3629-416b-8352-d17a877a1835" />
<img width="1919" height="1000" alt="Screenshot 2025-07-16 161752" src="https://github.com/user-attachments/assets/ae9bd529-b794-4835-83b1-f0140cd7f15e" />

---

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute to this project, please fork the repository and submit a pull request. Ensure your changes are well-documented and follow the project's coding standards.

---

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## 📬 Contact

For questions, suggestions, or feedback, please contact the maintainers at [agarwaldivyansh4002@gmail.com](mailto:agarwaldivyansh4002@gmail.com).

---

## 💖 Thanks Message

A heartfelt thank you to all contributors and users who have supported this project. Special thanks to Google for their Generative AI capabilities, which power the feature suggestion engine.

---

This README was generated with ❤️ by readme.ai.
