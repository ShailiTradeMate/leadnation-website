// One-off mechanical migration: preserve every option, prop and change handler.
const fs = require('fs');
const path = require('path');
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(file);
    else if (file.endsWith('.jsx')) {
      const source = fs.readFileSync(file, 'utf8');
      if (!source.includes('<select')) continue;
      const migrated = source.replace(/<(\/?)select\b/g, '<$1ResponsiveSelect');
      fs.writeFileSync(file, `import { ResponsiveSelect } from '@/components/ui/responsive-select';\n${migrated}`);
      console.log(path.relative(process.cwd(), file));
    }
  }
}
walk(path.join(__dirname, '../src/pages'));