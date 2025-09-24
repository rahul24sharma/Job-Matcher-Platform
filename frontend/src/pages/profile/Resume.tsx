// src/pages/Resume.tsx
import React, { useState, useCallback, useEffect } from 'react';
import { Upload, FileText, Check, AlertCircle, Loader2, Download, Trash2, Eye } from 'lucide-react';
// import { resumeApi } from '../api/resume.api';
import { resumeApi } from '../../api/resume.api';
// import { useAuthStore } from '../store/authStore';
import { useAuthStore } from '../../store/authStore';

type UploadedResumeMeta = {
  name: string;
  size: string;       // "123.45 KB"
  uploadedAt: string; // ISO
  type: string;       // mime-type
};

const Resume: React.FC = () => {
  const token = useAuthStore((s) => s.token); // ensures we wait for auth if you want
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [uploadedResume, setUploadedResume] = useState<UploadedResumeMeta | null>(null);
  const [extractedSkills, setExtractedSkills] = useState<string[]>([]);
  const [alert, setAlert] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (!token) return; // optional: wait for auth
    const resumeData = localStorage.getItem('uploadedResume');
    if (resumeData) {
      try {
        setUploadedResume(JSON.parse(resumeData));
        console.log(resumeData)
      } catch {}
    }
  }, [token]);

  const showAlert = (message: string, type: 'success' | 'error' = 'success') => {
    setAlert({ message, type });
    setTimeout(() => setAlert(null), 3000);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleResumeUpload(files[0]);
    }
  }, []);

  const handleResumeUpload = async (file: File) => {
    if (!file || !/\.(pdf|doc|docx)$/i.test(file.name)) {
      showAlert('Please upload a PDF or Word document', 'error');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      showAlert('File size should be less than 5MB', 'error');
      return;
    }

    setLoading(true);
    try {
      const resp = await resumeApi.upload(file);

      const meta: UploadedResumeMeta = {
        name: file.name,
        size: (file.size / 1024).toFixed(2) + ' KB',
        uploadedAt: new Date().toISOString(),
        type: file.type || 'application/octet-stream',
      };
      setUploadedResume(meta);
      localStorage.setItem('uploadedResume', JSON.stringify(meta));

      if (resp.skills?.length) {
        setExtractedSkills(resp.skills);
        showAlert(`Resume uploaded! Found ${resp.skills.length} skills`, 'success');
      } else {
        showAlert('Resume uploaded successfully!', 'success');
      }
    } catch (err) {
      showAlert('Failed to upload resume. Please try again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleResumeUpload(file);
  };

  const deleteResume = () => {
    if (window.confirm('Are you sure you want to delete your resume?')) {
      setUploadedResume(null);
      setExtractedSkills([]);
      localStorage.removeItem('uploadedResume');
      showAlert('Resume deleted', 'success');
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

    

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 p-6">
      {alert && (
        <div className="fixed top-4 right-4 z-50">
          <div className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg ${alert.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>
            {alert.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
            <span>{alert.message}</span>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8 flex items-center gap-3">
          <FileText className="text-blue-400" />
          Resume Management
        </h1>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h2 className="text-2xl font-semibold text-white mb-6">Upload Your Resume</h2>

          {!uploadedResume ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-all ${
                isDragging ? 'border-blue-400 bg-blue-500/20' : 'border-white/30 hover:border-white/50'
              }`}
            >
              {loading ? (
                <div className="flex flex-col items-center">
                  <Loader2 className="h-12 w-12 text-blue-400 animate-spin mb-4" />
                  <p className="text-white">Processing your resume...</p>
                </div>
              ) : (
                <>
                  <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                  <p className="text-white text-lg mb-2">Drag and drop your resume here</p>
                  <p className="text-gray-400 mb-6">or</p>
                  <label className="inline-block px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg cursor-pointer transition-colors font-medium">
                    Browse Files
                    <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileInput} className="hidden" />
                  </label>
                  <p className="text-gray-400 text-sm mt-4">Supported formats: PDF, DOC, DOCX (Max 5MB)</p>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-green-500/20 rounded-lg">
                      <FileText className="h-8 w-8 text-green-400" />
                    </div>
                    <div>
                      <h3 className="text-white font-medium text-lg">{uploadedResume.name}</h3>
                      <p className="text-gray-400 text-sm mt-1">
                        Size: {uploadedResume.size} • Uploaded: {formatDate(uploadedResume.uploadedAt)}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {/* TODO: wire these when you add a download/view route on backend */}
                    <button className="p-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors" title="View Resume">
                      <Eye size={18} />
                    </button>
                    <button className="p-2 bg-gray-500/20 hover:bg-gray-500/30 text-gray-400 rounded-lg transition-colors" title="Download Resume">
                      <Download size={18} />
                    </button>
                    <button onClick={deleteResume} className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors" title="Delete Resume">
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>

              {extractedSkills.length > 0 && (
                <div>
                  <h3 className="text-white font-medium mb-3">Extracted Skills</h3>
                  <div className="flex flex-wrap -m-1">
                  {extractedSkills.map((s, i) => (
    <React.Fragment key={s}>
      {s}{i < extractedSkills.length - 1 ? ' • ' : ''}
    </React.Fragment>
  ))}
</div>
                </div>
              )}

              <div className="flex justify-center">
                <label className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg cursor-pointer transition-colors font-medium">
                  Upload New Resume
                  <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileInput} className="hidden" />
                </label>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h3 className="text-xl font-semibold text-white mb-4">Resume Tips</h3>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <Check className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Keep your resume concise and limited to 1-2 pages</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Include relevant keywords that match job descriptions</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Highlight your achievements with quantifiable results</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="h-5 w-5 text-green-400 mt-0.5 flex-shrink-0" />
              <span>Ensure your contact information is up to date</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Resume;
