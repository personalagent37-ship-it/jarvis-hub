import json

log_path = '/home/talha/.gemini/antigravity/brain/04cc872f-980f-4c0b-a478-c0f0dbccf9fc/.system_generated/logs/overview.txt'
with open(log_path, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    # Search for the view_file response block
    if 'File Path: `file:///home/talha/Desktop/jartvis/jarvis_hub/public/index.html`' in line:
        output_lines = []
        for j in range(i+1, len(lines)):
            if 'The above content shows the entire' in lines[j] or 'The following code has been modified' in lines[j] or '"tool_calls"' in lines[j] or '{"step_index"' in lines[j]:
                break
            output_lines.append(lines[j])
        
        if len(output_lines) > 50:
            clean_lines = []
            for out_line in output_lines:
                if ':' in out_line and out_line.split(':')[0].strip().isdigit():
                    clean_lines.append(out_line.split(':', 1)[1][1:])
                else:
                    clean_lines.append(out_line)
            
            with open('/home/talha/Desktop/jartvis/jarvis_hub/public/index.html', 'w') as out_f:
                out_f.write(''.join(clean_lines))
            print(f'Recovered index.html with {len(clean_lines)} lines!')
            exit(0)

print('Could not find the view_file block in overview.txt')
