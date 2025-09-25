// pages/VerifyPage.tsx
import React, { useState } from 'react';
import { CertificateUpload } from '../components/CertificateUpload';
import { VerificationResult } from '../components/VerificationResult';
import { VerificationResult as VerificationResultType, CertificateData } from '../types';

export const VerifyPage = () => {
  const [verificationResult, setVerificationResult] = useState<VerificationResultType | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Dataset that we can allow uploading or pre-fill with CSV
  const [dataset, setDataset] = useState<CertificateData[]>([]);

  const handleVerification = async (file: File) => {
    setIsLoading(true);

    // Simulate OCR extraction
    const extractedData: Partial<CertificateData> = {
      name: 'Unknown',
      rollNumber: 'Unknown',
      certificateId: 'Unknown',
      institution: 'Unknown',
      course: 'Unknown',
      grades: 'Unknown',
      issueDate: new Date().toISOString()
    };

    // Check dataset for match
    const match = dataset.find(d => d.certificateId === extractedData.certificateId);

    const result: VerificationResultType = match
      ? {
          status: 'authentic',
          extractedData: match,
          anomalies: [],
          confidence: 98.5,
          timestamp: new Date().toISOString()
        }
      : {
          status: 'invalid',
          extractedData: extractedData as CertificateData,
          anomalies: ['Data Not Available in our database'],
          confidence: 0,
          timestamp: new Date().toISOString()
        };

    setTimeout(() => {
      setVerificationResult(result);
      setIsLoading(false);
    }, 1500);
  };

  const handleDatasetUpload = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target?.result as string;
        const rows = text.split('\n').filter(Boolean);
        const headers = rows[0].split(',');
        const data: CertificateData[] = rows.slice(1).map(row => {
          const values = row.split(',');
          const obj: any = {};
          headers.forEach((h, i) => obj[h.trim()] = values[i]?.trim() || '');
          return obj as CertificateData;
        });
        setDataset(data);
        alert('Dataset loaded successfully!');
      } catch (err) {
        alert('Failed to load dataset!');
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center mb-4">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Verify Certificate Authenticity</h1>
        <p className="text-gray-600">Upload a certificate document to check against our database</p>
      </div>

      {/* Dataset Upload */}
      <div className="bg-gray-50 p-6 rounded-xl shadow-md mb-8 text-center">
        <h2 className="font-semibold text-gray-800 mb-2">Upload Dataset (CSV)</h2>
        <input
          type="file"
          accept=".csv"
          onChange={e => e.target.files && handleDatasetUpload(e.target.files[0])}
          className="border px-4 py-2 rounded-lg"
        />
        <p className="text-gray-500 text-sm mt-1">CSV columns: name,rollNumber,certificateId,institution,issueDate,course,grades</p>
      </div>

      <CertificateUpload onFileUpload={handleVerification} isLoading={isLoading} />

      {verificationResult && (
        <div className="mt-8">
          <VerificationResult result={verificationResult} />
        </div>
      )}
    </div>
  );
};
