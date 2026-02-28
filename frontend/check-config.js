#!/usr/bin/env node
/**
 * API Configuration Diagnostic Script
 * Run this script to check if your frontend is properly configured to use Vite proxy
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 API Configuration Diagnostic\n');
console.log('='.repeat(60));

// Check current directory
const cwd = process.cwd();
console.log(`📁 Current directory: ${cwd}`);

// Check if we're in the frontend directory
const isInFrontend = cwd.includes('frontend') || fs.existsSync(path.join(cwd, 'src', 'api'));
console.log(`   In frontend directory: ${isInFrontend ? '✅' : '❌'}`);

// Find .env files
const envFiles = ['.env', '.env.local', '.env.development', '.env.production'];
console.log('\n📄 Environment Files:');

let envContent = null;
const envPath = path.join(cwd, '.env');

if (fs.existsSync(envPath)) {
  envContent = fs.readFileSync(envPath, 'utf-8');
  console.log('✅ .env found');
  envContent.split('\n').forEach(line => {
    if (line.trim() && !line.startsWith('#')) {
      console.log(`   ${line}`);
    }
  });
} else {
  console.log('❌ .env NOT found');
}

// Check vite.config.ts
const viteConfigPath = path.join(cwd, 'vite.config.ts');
console.log('\n⚙️  Vite Config:');

if (fs.existsSync(viteConfigPath)) {
  console.log('✅ vite.config.ts found');
  const viteConfig = fs.readFileSync(viteConfigPath, 'utf-8');

  if (viteConfig.includes("proxy:")) {
    console.log('✅ Proxy configured');

    if (viteConfig.includes("target: 'http://localhost:8000'") ||
        viteConfig.includes('target: "http://localhost:8000"')) {
      console.log('✅ Proxy target: http://localhost:8000');
    }

    if (viteConfig.includes("'/api':") || (viteConfig.includes('"/api":'))) {
      console.log('✅ Proxy pattern: /api');
    }
  } else {
    console.log('❌ Proxy NOT configured');
  }
} else {
  console.log('❌ vite.config.ts NOT found');
}

// Check client.ts
const clientPath = path.join(cwd, 'src', 'api', 'client.ts');
console.log('\n🔧 API Client:');

if (fs.existsSync(clientPath)) {
  console.log('✅ src/api/client.ts found');
  const clientContent = fs.readFileSync(clientPath, 'utf-8');

  // Check for absolute URLs
  const hasAbsoluteUrl = clientContent.includes('http://localhost:8000') ||
                         clientContent.includes('https://localhost:8000');

  if (hasAbsoluteUrl) {
    console.log('❌ ERROR: Hardcoded localhost:8000 URL found in client.ts!');
    console.log('   This will bypass the Vite proxy.');
  } else {
    console.log('✅ No hardcoded URLs found');
  }

  // Check for relative baseURL
  if (clientContent.includes("VITE_API_BASE_URL")) {
    console.log('✅ Using VITE_API_BASE_URL environment variable');
  }
} else {
  console.log('❌ src/api/client.ts NOT found');
}

// Diagnosis
console.log('\n' + '='.repeat(60));
console.log('📋 Diagnosis:\n');

if (envContent) {
  if (envContent.includes('http://localhost:8000') ||
      envContent.includes('https://localhost:8000')) {
    console.log('❌ PROBLEM FOUND: .env contains absolute URL');
    console.log('   Solution: Change to relative path');
    console.log('   Current: VITE_API_BASE_URL=http://localhost:8000/api/v1');
    console.log('   Should be: VITE_API_BASE_URL=/api/v1');
  } else if (envContent.includes('VITE_API_BASE_URL=/api/v1') ||
             envContent.includes('VITE_API_BASE_URL=/api')) {
    console.log('✅ .env is correctly configured with relative path');
  } else {
    console.log('⚠️  .env exists but VITE_API_BASE_URL may not be set correctly');
  }
} else {
  console.log('❌ PROBLEM: .env file not found');
  console.log('   Solution: Create .env with VITE_API_BASE_URL=/api/v1');
}

console.log('\n' + '='.repeat(60));
console.log('🔧 Next Steps:\n');
console.log('1. Stop the Vite dev server (Ctrl+C)');
console.log('2. Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)');
console.log('3. Clear localStorage: localStorage.clear()');
console.log('4. Restart dev server: npm run dev');
console.log('5. Check browser console for "🔧 API Configuration" log');
console.log('6. Verify requests show: Request URL: http://localhost:5173/api/v1/...');
console.log('='.repeat(60));
