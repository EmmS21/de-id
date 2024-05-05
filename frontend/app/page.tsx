'use client'

import Image from "next/image";
import { useState } from "react";
import ClipLoader from "react-spinners/ClipLoader";

export default function Home() {
  const [sampleData, setSampleData] = useState('');
  const [clearData, setClearData] = useState('');
  const [deIdData, setDeIdData] = useState('');
  const [isLoading, setIsLoading] = useState(false); 

  const formatText = (text: string) => {
    const parts = text.split(/\*\*([^*]+)\*\*/g);

    // Iterate through the parts and format them
    const formattedParts = parts.map((part, index) => {
      if (index % 2 === 0) {
        return <div key={index}>{part}</div>;
      } else {
        return <div key={index} style={{ color: 'blue', fontWeight: 'bold' }}>{part}</div>;
      }
    });
    return formattedParts;
  };


  const fetchSampleData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/sample-data');
      const jsonData = await response.json();
      const dataText = jsonData.data; 
      setClearData(dataText)
      const formattedData = formatText(dataText); // Format the text with HTML elements
      setSampleData(formattedData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setSampleData('Failed to load data.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDeIdentifiedData = async () => {
    setIsLoading(true);
    try {
        let formattedSampleData = '';
        if (Array.isArray(sampleData)) {
            // Format the sample data
            formattedSampleData = sampleData.map((element) => element.props.children).join('\n');
        } else {
            formattedSampleData = sampleData;
        }
        const requestData = {
            clinical_text: formattedSampleData
        };
        const response = await fetch('http://127.0.0.1:8000/deidentify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        const jsonData = await response.json();
        // Format the de-identified text
        let deIdentifiedText = jsonData.deidentified_text;

        // Remove <s> and </s> if present
        if (deIdentifiedText.startsWith('<s>') && deIdentifiedText.endsWith('</s>')) {
            deIdentifiedText = deIdentifiedText.substring(3, deIdentifiedText.length - 4).trim();
        }

        const sections = deIdentifiedText.split('\n\n'); // Split by double newline
        const formattedSections = sections.map((section, index) => {
            const lines = section.split('\n'); // Split each section by newline
            return (
                <div key={index}>
                    {lines.map((line, lineIndex) => {
                        const trimmedLine = line.trim();
                        const isTitleSection = [
                            'Patient Information:',
                            'Referring Physician:',
                            'Radiology Examination:',
                            'Clinical Indication:',
                            'Technique:',
                            'Findings:',
                            'Impression:',
                            'Recommendation:',
                            'Radiologist:',
                            'Date of Report:'
                        ].includes(trimmedLine);
                        return isTitleSection ? (
                            <div key={lineIndex} style={{ color: 'blue', fontWeight: 'bold' }}>
                                {trimmedLine}
                            </div>
                        ) : (
                            <div key={lineIndex}>{line}</div>
                        );
                    })}
                </div>
            );
        });

        setDeIdData(formattedSections);
    } catch (error) {
        console.error('Failed to fetch de-identified data:', error);
        setDeIdData('Failed to de-identify data.');
    } finally {
        setIsLoading(false);
    }
};

    
  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-8 pb-24 px-24 space-y-4">
      <div className="flex flex-col items-center space-y-4">
        <button 
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          onClick={fetchSampleData}
        >
          Sample Data
        </button>
        <div className="w-full p-32 bg-gray-100 rounded min-h-[16rem] max-h-[16rem] overflow-auto text-black flex flex-col items-start">
          {sampleData || ''}
        </div>
      </div>

      <div className="flex flex-col items-center space-y-4">
        <button 
          className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded ${sampleData ? '' : 'cursor-not-allowed opacity-50'}`} 
          onClick={fetchDeIdentifiedData}
          disabled={!sampleData}
        >
          De-Id
        </button>
        <div className="w-full p-32 bg-gray-100 rounded min-h-[16rem] max-h-[16rem] overflow-auto text-black flex flex-col items-start">
          {isLoading ? <ClipLoader color="#36d7b7" /> : (deIdData || 'De-identified JSON will appear here...')}
        </div>
      </div>
    </main>
  );
}
