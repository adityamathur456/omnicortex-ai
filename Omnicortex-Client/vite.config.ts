import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import type { Connect, PreviewServer, ViteDevServer } from 'vite';

function safeFilename(filename: string) {
  return filename.replace(/[^a-zA-Z0-9._-]/g, '_');
}

function attachDownloadProxy(middlewares: Connect.Server) {
  middlewares.use('/__download', async (req, res) => {
    const requestUrl = new URL(req.url || '', 'http://127.0.0.1');
    const targetUrl = requestUrl.searchParams.get('url');
    const requestedFilename = requestUrl.searchParams.get('filename') || 'download';

    if (!targetUrl) {
      res.statusCode = 400;
      res.end('Missing url parameter.');
      return;
    }

    try {
      const upstream = await fetch(targetUrl);

      if (!upstream.ok || !upstream.body) {
        res.statusCode = upstream.status || 502;
        res.end('Unable to fetch remote file.');
        return;
      }

      const contentType =
        upstream.headers.get('content-type') || 'application/octet-stream';

      res.statusCode = 200;
      res.setHeader('Content-Type', contentType);
      res.setHeader(
        'Content-Disposition',
        `attachment; filename="${safeFilename(requestedFilename)}"`,
      );

      const arrayBuffer = await upstream.arrayBuffer();
      res.end(Buffer.from(arrayBuffer));
    } catch {
      res.statusCode = 502;
      res.end('Download proxy failed.');
    }
  });
}

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'omnicortex-download-proxy',
      configureServer(server: ViteDevServer) {
        attachDownloadProxy(server.middlewares);
      },
      configurePreviewServer(server: PreviewServer) {
        attachDownloadProxy(server.middlewares);
      },
    },
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '127.0.0.1',
  },
});
