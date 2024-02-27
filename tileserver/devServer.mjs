import Fastify from 'fastify'
import cors from '@fastify/cors';
import { getVectorTiles as getRGDVectorTiles } from './rgd.mjs';
import { getVectorTiles as getScoringVectorTiles } from './scoring.mjs';

const fastify = Fastify({ logger: true });
await fastify.register(cors);

fastify.get('/api/vector-tiles/tile.pbf', async (request, reply) => {
  const { modelRunId, z, x, y, randomKey } = request.query;

  const vectorTileData = await getRGDVectorTiles(modelRunId, z, x, y, randomKey);

  reply.header('Content-Type', 'application/octet-stream');
  reply.code(vectorTileData.length === 0 ? 204 : 200);

  reply.send(vectorTileData);
});

fastify.get('/api/scoring/vector-tiles/tile.pbf', async (request, reply) => {
  const { modelRunId, z, x, y } = request.query;

  const vectorTileData = await getScoringVectorTiles(modelRunId, z, x, y);

  reply.header('Content-Type', 'application/octet-stream');
  reply.code(vectorTileData.length === 0 ? 204 : 200);

  reply.send(vectorTileData);
});

// Start the server
fastify.listen({ port: process.env.PORT, host: '0.0.0.0' }).then((address) => {
  console.log(`Server listening on ${address}`);
});
