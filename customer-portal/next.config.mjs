/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Ensure that env variables used at build time are passed
  // Any public env variables should be prefixed with NEXT_PUBLIC_
};

export default nextConfig;
