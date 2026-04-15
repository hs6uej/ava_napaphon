/** @type {import('next').NextConfig} */
import path from 'path';

const nextConfig = {
  output: 'standalone',
  // Ensure that env variables used at build time are passed
  // Any public env variables should be prefixed with NEXT_PUBLIC_
  webpack: (config) => {
    config.resolve.alias['@'] = path.resolve(__dirname, 'src');
    return config;
  },
};

export default nextConfig;
