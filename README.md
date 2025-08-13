
# Faculty New Joiners Onboarding Hub


A comprehensive help desk system for CSE (Computer Science and Engineering) students and staff, featuring AI-powered chat support, document search, and user management capabilities.

## Features

### Core Functionality

* **AI Chat Support**: Intelligent chatbot powered by Qwen/QwQ-32B model
* **Document Search**: RAG-based search system for PDF documents
* **User Management**: Role-based access control (Student, Staff, Admin)
* **File Management**: PDF upload, storage, and retrieval system
* **Session Management**: Persistent chat history and session tracking
* **Feedback System**: User feedback collection and management

### User Roles

* **Staff**: Access to AI chat and document search
* **Administrators**: Full system control and user management

## Architecture

### Frontend

* **React 19** with modern hooks and functional components
* **Material-UI (MUI)** for consistent and responsive design
* **React Router** for navigation and route protection
* **Vite** for fast development and building
* **Responsive Design** supporting both desktop and mobile

### Backend

* **Flask** web framework with RESTful API design
* **MySQL** database for persistent data storage
* **RAG System** using FAISS and Sentence Transformers
* **JWT Authentication** for secure user sessions
* **CORS Support** for cross-origin requests
* **File Upload** handling with secure filename processing

### AI Integration

* **SiliconFlow API** integration for AI chat
* **Qwen/QwQ-32B** language model
* **RAG Pipeline** for document-based question answering
* **Semantic Search** using sentence embeddings

## Project Structure

```
capstone-project-25t2-9900-f16a-cake/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── utils/          # Utility functions
│   │   └── App.jsx         # Main application component
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── backend/                 # Flask backend application
│   ├── AI/                 # AI chat API endpoints
│   ├── rag/                # RAG system files and indexes
│   ├── pdfs/               # PDF document storage
│   ├── app.py              # Main Flask application
│   ├── database.py         # Database operations
│   ├── search.py           # Search functionality
│   └── config.json         # Configuration file
└── README.md               # This file
```

## Installation

### Prerequisites

* Python 3.8+
* Node.js 18+
* MySQL 8.0+
* Git

### Backend Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd capstone-project-25t2-9900-f16a-cake/backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**

   ```bash
   pip install flask flask-cors flask-mail mysql-connector-python
   pip install pdfplumber faiss-cpu sentence-transformers
   pip install requests pyjwt
   ```

4. **Database Setup**

   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE chat_system;

   # Import schema
   mysql -u root -p chat_system < chat_system.sql
   ```

5. **Configure database connection**

   * Edit `database.py` with your MySQL credentials
   * Update `db_config` dictionary

6. **Start backend server**

   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**

   ```bash
   cd ../frontend
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Start development server**

   ```bash
   npm run dev
   ```

## Configuration

### Backend Configuration

* **Database**: Update `database.py` with your MySQL settings
* **AI API**: Configure API keys in `AI/api.py`
* **Email**: Update SMTP settings in `app.py`
* **File Storage**: Configure upload paths and allowed extensions

### Frontend Configuration

* **API Endpoints**: Update backend URL in API calls
* **Environment Variables**: Configure any required environment variables

## Usage

### Starting the System

1. Start the backend server: `python app.py`
2. Start the frontend: `npm run dev`
3. Access the application at `http://localhost:5173`

### User Workflow

1. **Login**: Use provided credentials for your role
2. **AI Chat**: Ask questions and receive AI-powered responses
3. **Document Search**: Search through uploaded PDF documents
4. **File Management**: Upload and manage PDF files (Staff/Admin)
5. **Session Management**: View chat history and manage sessions

## Testing

### Backend Testing

* **Stress Testing**: Use `clean_stress_test.py` for API performance testing
* **Endpoint Testing**: Test individual API endpoints
* **Database Testing**: Verify database operations

### Frontend Testing

* **Component Testing**: Test individual React components
* **Integration Testing**: Test user workflows
* **Responsive Testing**: Test on different screen sizes

## Performance

### System Requirements

* **CPU**: 4+ cores recommended for RAG operations
* **Memory**: 8GB+ RAM for optimal performance
* **Storage**: SSD recommended for faster file operations
* **Network**: Stable internet connection for AI API calls

### Optimization Features

* **RAG Indexing**: Pre-built document indexes for fast search
* **Connection Pooling**: Efficient database connection management
* **Async Operations**: Non-blocking API calls
* **Caching**: Session and user data caching

## Security Features

* **JWT Authentication**: Secure token-based authentication
* **Role-based Access Control**: Granular permission system
* **Input Validation**: Comprehensive input sanitization
* **Secure File Upload**: File type and size validation
* **CORS Protection**: Cross-origin request security

## API Documentation

### Authentication Endpoints

* `POST /api/login` - User authentication
* `POST /api/logout` - User logout

### Chat Endpoints

* `POST /api/chat` - AI chat interaction
* `GET /api/sessions` - Get user sessions
* `POST /api/sessions` - Create new session

### Search Endpoints

* `POST /api/search` - Document search
* `GET /api/documents` - List available documents

### File Management

* `POST /api/upload` - Upload PDF files
* `GET /api/files` - List uploaded files
* `DELETE /api/files/<id>` - Delete files

## Team

* **Team**: capstone-project-25t2-9900-f16a-cake
* **Course**: COMP9900 
* **Institution**: UNSW Sydney
* **Term**: 25T2

## Support

For technical support or questions:

* Check the documentation
* Review the code comments
* Contact the development team

