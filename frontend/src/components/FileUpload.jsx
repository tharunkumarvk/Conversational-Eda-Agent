// src/components/FileUpload.jsx
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';
import '../styles/FileUpload.css';

function FileUpload({ onFilesSelected }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: onFilesSelected,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    multiple: false,
    maxSize: 104857600, // 100MB
  });

  return (
    <div {...getRootProps()} className={`file-upload ${isDragActive ? 'drag-active' : ''}`}>
      <input {...getInputProps()} />
      <div className="upload-content">
        {isDragActive ? (
          <>
            <Upload size={48} className="upload-icon active" />
            <p>Drop the file here...</p>
          </>
        ) : (
          <>
            <FileText size={48} className="upload-icon" />
            <p>Drag & drop a file here, or click to select</p>
            <p className="upload-hint">Supported formats: CSV, Excel (.xlsx, .xls)</p>
            <p className="upload-hint">Maximum file size: 100MB</p>
          </>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
