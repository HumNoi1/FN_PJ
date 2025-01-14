// services/FileService.js
import supabase from '@/lib/supabase';

export class FileService {
    // กำหนดประเภทไฟล์ที่ยอมรับได้
    static FILE_TYPES = {
        TEACHER: 'teacher',
        STUDENT: 'student'
    };

    // เมธอดสำหรับตรวจสอบความถูกต้องของประเภทไฟล์
    static validateFileType(fileType) {
        if (!Object.values(this.FILE_TYPES).includes(fileType)) {
            throw new Error('Invalid file type. Must be either "teacher" or "student"');
        }
        return fileType;
    }

    // เมธอดสำหรับสร้าง bucket path
    static getBucketPath(fileType) {
        const validatedType = this.validateFileType(fileType);
        return `${validatedType}-files`;
    }

    // เมธอดหลักสำหรับอัปโหลดไฟล์
    static async uploadFile(file, fileType) {
        try {
            // ตรวจสอบว่ามีไฟล์และประเภทไฟล์ถูกส่งมา
            if (!file) {
                throw new Error('No file provided');
            }

            // ตรวจสอบประเภทไฟล์
            const validatedType = this.validateFileType(fileType);

            // ตรวจสอบนามสกุลไฟล์
            if (!file.type.includes('pdf')) {
                throw new Error('Only PDF files are allowed');
            }

            // ตรวจสอบขนาดไฟล์ (จำกัดที่ 5MB)
            const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB in bytes
            if (file.size > MAX_FILE_SIZE) {
                throw new Error('File size exceeds 5MB limit');
            }

            // สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
            const fileName = `${Date.now()}_${file.name.replace(/\s+/g, '_')}`;
            const bucketPath = this.getBucketPath(validatedType);

            // อัปโหลดไฟล์ไปยัง Supabase Storage
            const { data: storageData, error: storageError } = await supabase.storage
                .from(bucketPath)
                .upload(fileName, file, {
                    cacheControl: '3600',
                    upsert: false
                });

            if (storageError) {
                throw new Error(`Storage error: ${storageError.message}`);
            }

            // สร้าง public URL
            const { data: urlData } = supabase.storage
                .from(bucketPath)
                .getPublicUrl(fileName);

            // บันทึกข้อมูลในฐานข้อมูล
            const { data: fileRecord, error: dbError } = await supabase
                .from('files')
                .insert({
                    name: file.name,
                    type: validatedType,
                    storage_path: fileName,
                    url: urlData.publicUrl,
                    status: 'pending_embedding'
                })
                .select()
                .single();

            if (dbError) {
                throw new Error(`Database error: ${dbError.message}`);
            }

            return fileRecord;

        } catch (error) {
            console.error('Upload error:', error);
            throw error;
        }
    }

    static async testConnection() {
        try {
            // ทดสอบการเชื่อมต่อโดยการดึงข้อมูลจากตาราง files
            const { data, error } = await supabase
                .from('files')
                .select('count')
                .limit(1);
    
            if (error) {
                throw error;
            }
    
            return { success: true, message: 'Successfully connected to Supabase' };
        } catch (error) {
            console.error('Connection test failed:', error);
            return { success: false, message: error.message };
        }
    }
}