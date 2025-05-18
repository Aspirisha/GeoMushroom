export default {
  base: "/geomushroom/", // GitHub Pages will serve under /<repo-name>/
  build: {
    outDir: '../../docs',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        app: './geomushroom.html', // default
      },
    },
  },
};
