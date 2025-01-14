/** @type {import('next').NextConfig} */
const nextConfig = {

    async rewrites() {
        return [
          {
            source: '/api/:path*',
            destination: 'http://localhost:5001/api/:path*',
          },
        ];
      },
      // เพิ่มการตั้งค่าอื่นๆ ที่จำเป็น
      reactStrictMode: true,
};

export default nextConfig;
