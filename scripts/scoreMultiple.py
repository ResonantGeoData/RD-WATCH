import os
import argparse
import subprocess
# script allows for scoring/uploading multiple scores when there is a root folder
# and each sub folder has a site_models and a region_models folder.
# it is intended to be run at a root location where the scoring folder exists, the annotations folder
# exists for ground truth and the metrics-and-test-framework folder exists as well.

database_URI = 'postgresql+psycopg2://scoring:secretkey@localhost:5433/scoring'
ground_truth = '../annotations/site_models'

def main(args):
    folder_path = args.folder
    performer = args.performer
    eval_run = args.eval_run
    eval_run_num = args.eval_run_num

    commands = []

    for root, _, _ in os.walk(folder_path):
        site_models_path = os.path.join(root, 'site_models')
        region_models_path = os.path.join(root, 'region_models')
        
        if os.path.isdir(site_models_path):
            geojson_files = [file for file in os.listdir(site_models_path) if file.endswith('.geojson')]
            
            if geojson_files:
                first_geojson = geojson_files[0]
                identifier = first_geojson[:7]
                module_path = os.path.join('iarpa_smart_metrics', 'run_evaluation')

                subprocess_args = [
                    'python', '-m', 'iarpa_smart_metrics.run_evaluation',
                    '--roi', identifier,
                    '--gt_dir', ground_truth,
                    '--rm_dir', region_models_path.replace('./', '../'),
                    '--sm_dir', site_models_path.replace('./', '../'),
                    '--output_dir', f'../{identifier}/output',
                    '--eval_num', str(eval_run),
                    '--eval_run_num', str(eval_run_num),
                    '--performer', performer,
                    '--no-viz',
                    '--no-viz-detection-table',
                    '--no-viz-comparison-table',
                    '--no-viz-associate-metrics',
                    '--no-viz-activity-metrics',
                    '--sequestered_id', identifier,
                    '--db_conn_str', database_URI,
                ]

                if args.output_commands:  # Check if the flag is provided
                    command_string = ' '.join(subprocess_args)
                    commands.append(command_string)
                else:
                    process = subprocess.Popen(subprocess_args, cwd='./metrics-and-test-framework', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    stdout, stderr = process.communicate()

                    # Print subprocess output to script's stdout
                    print("Subprocess stdout:")
                    print(stdout)
                    print("Subprocess stderr:")
                    print(stderr)

    if args.output_commands:
        # Save the formatted commands to the file
        with open('scoring_commands.txt', 'w') as f:
            for idx, cmd in enumerate(commands, start=1):
                f.write(f"Command {idx}:\n{cmd}\n{'='*40}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process folders and run evaluation subprocess.')
    parser.add_argument('--folder', type=str, help='Main folder path')
    parser.add_argument('--performer', type=str, help='Performer name')
    parser.add_argument('--eval_run', type=int, help='Evaluation run number')
    parser.add_argument('--eval_run_num', type=int, help='Evaluation run number')
    parser.add_argument('--output_commands', action='store_true', help='Output commands instead of executing subprocesses')
    args = parser.parse_args()
    
    main(args)
