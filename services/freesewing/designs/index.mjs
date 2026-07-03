import { Shirt } from './shirt.mjs';
import { Jacket } from './jacket.mjs';
import { Pants } from './pants.mjs';
import { Skirt } from './skirt.mjs';
import { Dress } from './dress.mjs';

const DESIGNS = {
  shirt: Shirt,
  jacket: Jacket,
  pants: Pants,
  skirt: Skirt,
  dress: Dress,
};

const DESIGN_INFO = {
  shirt: {
    name: 'Shirt',
    type: 'shirt',
    pieces: ['Front', 'Back', 'Sleeve', 'Collar', 'Collar Stand'],
    gender: 'all',
  },
  jacket: {
    name: 'Jacket',
    type: 'jacket',
    pieces: ['Front', 'Back', 'Sleeve'],
    gender: 'all',
  },
  pants: {
    name: 'Pants',
    type: 'pants',
    pieces: ['Front', 'Back'],
    gender: 'all',
  },
  skirt: {
    name: 'Skirt',
    type: 'skirt',
    pieces: ['Front', 'Back'],
    gender: 'female',
  },
  dress: {
    name: 'Dress',
    type: 'dress',
    pieces: ['Front', 'Back'],
    gender: 'female',
  },
};

export { DESIGNS, DESIGN_INFO };
