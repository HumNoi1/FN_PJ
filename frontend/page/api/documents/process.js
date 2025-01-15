// pages/api/documents/process.js
import { NextApiRequest, NextApiResponse } from 'next';
import formidable from 'formidable';
import fetch from 'node-fetch';

export const config = {
    api: {
        bodyParser: false, // จำเป็นสำหรับ formidable
    },
};

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method Not Allowed' });
    }

    try {
        const form = new formidable.IncomingForm();
        const { fields, files } = await new Promise((resolve, reject) => {
            form.parse(req, (err, fields, files) => {
                if (err) reject(err);
                resolve({ fields, files });
            });
        });

        // สร้าง FormData ใหม่เพื่อส่งไปยัง Flask backend
        const formData = new FormData();
        formData.append('file', files.file);
        formData.append('document_id', fields.document_id);
        formData.append('file_type', fields.file_type);

        // ส่งต่อไปยัง Flask backend
        const backendResponse = await fetch('http://localhost:5000/process', {
            method: 'POST',
            body: formData,
        });

        const data = await backendResponse.json();
        return res.status(backendResponse.status).json(data);

    } catch (error) {
        console.error('Error processing document:', error);
        return res.status(500).json({ error: 'Internal Server Error' });
    }
}