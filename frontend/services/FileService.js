// services/FileService.js
export class FileService {
    static FILE_TYPES = {
        TEACHER: 'teacher',
        STUDENT: 'student'
    };

    static async uploadFile(file, fileType) {
        try {
            // อัปโหลดไฟล์ไปยัง storage (เช่น Supabase Storage)
            const { data, error } = await supabase.storage
                .from('documents')
                .upload(`${fileType}/${file.name}`, file);

            if (error) throw error;

            // สร้าง record ในฐานข้อมูล
            const { data: fileRecord, error: dbError } = await supabase
                .from('files')
                .insert([{
                    name: file.name,
                    type: fileType,
                    url: data.path,
                    status: 'processing'
                }])
                .single();

            if (dbError) throw dbError;

            return fileRecord;

        } catch (error) {
            console.error('Error uploading file:', error);
            throw error;
        }
    }

    static async deleteFile(fileId) {
        // ลบไฟล์และ record ที่เกี่ยวข้อง
        try {
            const { error } = await supabase
                .from('files')
                .delete()
                .match({ id: fileId });

            if (error) throw error;

            return true;
        } catch (error) {
            console.error('Error deleting file:', error);
            throw error;
        }
    }
}