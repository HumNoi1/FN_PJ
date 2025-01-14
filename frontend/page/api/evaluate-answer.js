// pages/api/evaluate-answer.js
import axios from 'axios';

export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ message: 'Method not allowed' });
    }

    try {
        // เรียก Flask API
        const response = await axios.post(
            `${process.env.FLASK_API_URL}/evaluation/evaluate-answer`,
            req.body
        );
        
        return res.status(200).json(response.data);
    } catch (error) {
        console.error('Error calling Flask API:', error);
        return res.status(500).json({ 
            message: 'Failed to evaluate answer',
            error: error.message 
        });
    }
}