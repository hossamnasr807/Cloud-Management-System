import tkinter as tk
from tkinter import messagebox, filedialog
import os
import subprocess
import docker
import json
from datetime import datetime
import logging
import time

# Initialize Logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='cloud_management_system.log',
    filemode='a'
)

# Initialize Docker client
docker_client = docker.from_env()

def create_vm_gui():
    logging.info("Create VM GUI function initiated.")

    def handle_option_selection():
        selected_option = option_var.get()
        logging.debug(f"Option selected: {selected_option}")

        if selected_option == "existing":
            # Enable existing image fields and CPU/Memory fields, disable disk size field
            existing_image_entry.config(state="normal")
            browse_button.config(state="normal")
            cpu_entry.config(state="normal")
            memory_entry.config(state="normal")
            disk_size_entry.config(state="disabled")
            logging.info("Existing image option selected. Enabled existing image fields.")
        
        elif selected_option == "new":
            # Enable new configuration fields, disable existing image fields
            existing_image_entry.config(state="disabled")
            browse_button.config(state="disabled")
            cpu_entry.config(state="normal")
            memory_entry.config(state="normal")
            disk_size_entry.config(state="normal")
            if config_var.get():
                load_config_values()
            logging.info("New configuration option selected. Enabled new configuration fields.")

    def browse_image():
        filepath = filedialog.askopenfilename(title="Select Existing Image", filetypes=[("QCOW2 Files", "*.qcow2")])
        if filepath:
            logging.info(f"Selected image file: {filepath}")
            existing_image_var.set(filepath)
        else:
            logging.warning("No file selected for existing image.")
            messagebox.showwarning("No File Selected", "No file was selected for the existing image.")

    def browse_config():
        config_file = filedialog.askopenfilename(title="Select Configuration File", filetypes=[("JSON Files", "*.json")])
        if config_file:
            config_var.set(config_file)
            logging.info(f"Selected configuration file: {config_file}")
            load_config_values()
        else:
            logging.warning("No configuration file selected.")
            messagebox.showwarning("No File Selected", "No configuration file was selected.")
            
    def load_config_values():
        """Load configuration file and populate input fields."""
        config_file = config_var.get()
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Populate fields based on the config file
                cpu_var.set(config.get("cpu", ""))
                memory_var.set(config.get("memory", ""))
                disk_size_var.set(config.get("disk_size", ""))
                logging.info(f"Loaded configuration values from {config_file}: {config}")
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_file}")
            messagebox.showerror("Error", "Configuration file not found.")
            
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON format in configuration file: {config_file}")
            messagebox.showerror("Error", "Invalid JSON format in configuration file.")

        except Exception as e:
            logging.error(f"Unexpected error loading configuration file: {e}")
            messagebox.showerror("Error", f"Failed to load configuration file: {e}")
            
        
    def create_vm():
        try:
            start_time = time.time()
            if option_var.get() == "existing":
                image_path = existing_image_var.get()
                if not os.path.exists(image_path):
                    messagebox.showerror("Error", "Selected image file does not exist.")
                    logging.error(f"Image file does not exist: {image_path}")
                    return

                # Fetch CPU and memory values from GUI fields
                cpu = cpu_var.get()
                memory = memory_var.get()

                # Validate CPU and memory inputs
                if not cpu.isdigit() or int(cpu) <= 0:
                    logging.error("Invalid CPU count entered.")
                    messagebox.showerror("Error", "Invalid CPU count.")
                    return
                if not memory.isdigit() or int(memory) <= 0:
                    logging.error("Invalid memory size entered.")
                    messagebox.showerror("Error", "Invalid memory size.")
                    return

                # Run QEMU command with user-specified CPU and memory
                command = f"qemu-system-x86_64 -m {memory}M -smp cpus={cpu} -hda {image_path} -boot c"
                logging.info(f"Running QEMU command: {command}")
                os.system(command)

                end_time = time.time()  # Record the end time
                duration = end_time - start_time  # Calculate the duration
                logging.info(f"Existing image VM creation completed in {duration:.2f} seconds.")  # Log the duration
                messagebox.showinfo("Success", f"Existing image VM created successfully in {duration:.2f} seconds.")

            elif option_var.get() == "new":
                cpu = cpu_var.get()
                memory = memory_var.get()
                disk_size = disk_size_var.get()

                # Validate inputs
                if not cpu.isdigit() or int(cpu) <= 0:
                    logging.error("Invalid CPU count entered.")
                    messagebox.showerror("Error", "Invalid CPU count.")
                    return
                if not memory.isdigit() or int(memory) <= 0:
                    logging.error("Invalid memory size entered.")
                    messagebox.showerror("Error", "Invalid memory size.")
                    return
                if not disk_size.isdigit() or int(disk_size) <= 0:
                    logging.error("Invalid memory size entered.")
                    messagebox.showerror("Error", "Invalid disk size.")
                    return

                # Prompt the user to select a save location for the disk image
                save_path = filedialog.asksaveasfilename(
                    title="Save Disk Image As",
                    initialfile=f"disk_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.qcow2",
                    filetypes=[("QCOW2 Files", "*.qcow2")],
                    defaultextension=".qcow2"
                )
                if not save_path:
                    logging.warning("No save location selected for disk image.")
                    messagebox.showerror("Error", "No save location selected.")
                    return

                # Create disk image at the selected location
                logging.info(f"Creating disk image at {save_path} with size {disk_size}MB.")
                os.system(f"qemu-img create -f qcow2 {save_path} {disk_size}M")

                # Prompt for ISO file
                iso_path = filedialog.askopenfilename(title="Select Boot ISO", filetypes=[("ISO Files", "*.iso")])
                if not iso_path:
                    logging.warning("No ISO file selected.")
                    messagebox.showerror("Error", "No ISO file selected.")
                    return

                # Run QEMU command to create a new VM
                command = f"qemu-system-x86_64 -m {memory}M -smp cpus={cpu} -hda {save_path} -cdrom {iso_path} -boot d"
                logging.info(f"Running QEMU command to create new VM: {command}")
                os.system(command)

                end_time = time.time()  # Record the end time
                duration = end_time - start_time  # Calculate the duration
                logging.info(f"VM creation completed in {duration:.2f} seconds.")  # Log the duration
                messagebox.showinfo("Success", f"VM created successfully in {duration:.2f} seconds.")

        except Exception as e:
            logging.error(f"Failed to create VM: {e}")
            messagebox.showerror("Error", f"Failed to create VM: {e}")



    # Create a new window (Toplevel) for VM creation
    vm_window = tk.Toplevel()
    vm_window.title("Create Virtual Machine")

    # Option selection
    option_var = tk.StringVar(value="existing")
    tk.Label(vm_window, text="Choose VM Creation Option:").pack(anchor="w")
    tk.Radiobutton(vm_window, text="Use Existing Image", variable=option_var, value="existing", command=handle_option_selection).pack(anchor="w")
    tk.Radiobutton(vm_window, text="Create New VM", variable=option_var, value="new", command=handle_option_selection).pack(anchor="w")

    # Existing image fields
    tk.Label(vm_window, text="Existing Image Path:").pack(anchor="w")
    existing_image_var = tk.StringVar()
    existing_image_entry = tk.Entry(vm_window, textvariable=existing_image_var, state="normal")
    existing_image_entry.pack(fill="x")
    browse_button = tk.Button(vm_window, text="Browse", command=browse_image)
    browse_button.pack()

    # Configuration file selection
    config_var = tk.StringVar()
    tk.Label(vm_window, text="Configuration File (Optional):").pack(anchor="w")
    config_entry = tk.Entry(vm_window, textvariable=config_var, state="normal")
    config_entry.pack(fill="x")
    browse_config_button = tk.Button(vm_window, text="Browse", command=browse_config)
    browse_config_button.pack()

    # New VM fields
    tk.Label(vm_window, text="CPU Count:").pack(anchor="w")
    cpu_var = tk.StringVar()
    cpu_entry = tk.Entry(vm_window, textvariable=cpu_var, state="normal")
    cpu_entry.pack()

    tk.Label(vm_window, text="Memory Size (MB):").pack(anchor="w")
    memory_var = tk.StringVar()
    memory_entry = tk.Entry(vm_window, textvariable=memory_var, state="normal")
    memory_entry.pack()

    tk.Label(vm_window, text="Disk Size (MB):").pack(anchor="w")
    disk_size_var = tk.StringVar()
    disk_size_entry = tk.Entry(vm_window, textvariable=disk_size_var, state="disabled")
    disk_size_entry.pack()

    # Create VM button
    create_button = tk.Button(vm_window, text="Create VM", command=create_vm)
    create_button.pack()


def create_dockerfile():
    logging.info("Create Dockerfile function initiated.")
    path = filedialog.askdirectory(title="Select Directory to Save Dockerfile")
    if not path:
        logging.warning("No file path selected for Dockerfile.")
        messagebox.showwarning("No Directory Selected", "No directory was selected to save the Dockerfile.")
        return

    def submit_dockerfile():
        content = text.get("1.0", "end").strip()
        dockerfile_path = os.path.join(path, "Dockerfile")
        start_time = time.time()  # Record the start time
        try:
            with open(dockerfile_path, 'w') as dockerfile:
                dockerfile.write(content)
            end_time = time.time()  # Record the end time
            duration = end_time - start_time  # Calculate the duration
            logging.info(f"Dockerfile created at {dockerfile_path} in {duration:.2f} seconds.")
            messagebox.showinfo("Success", f"Dockerfile created at {dockerfile_path} in {duration:.2f} seconds.")
        except Exception as e:
            logging.error(f"Failed to create Dockerfile: {e}")
            messagebox.showerror("Error", f"Failed to create Dockerfile: {e}")
        dockerfile_window.destroy()

    dockerfile_window = tk.Toplevel(root)
    dockerfile_window.title("Create Dockerfile")

    text = tk.Text(dockerfile_window, width=50, height=15)
    text.grid(row=0, column=0)

    submit_button = tk.Button(dockerfile_window, text="Submit", command=submit_dockerfile)
    submit_button.grid(row=1, column=0)


def build_docker_image():
    logging.info("Build Docker Image function initiated.")
    dockerfile_path = filedialog.askdirectory(title="Select Dockerfile Directory")
    if not dockerfile_path:
        messagebox.showwarning("No Directory Selected", "No directory was selected for the Dockerfile.")
        logging.warning("No directory selected for the Dockerfile.")
        return

    def submit_build():
        image_name = image_name_entry.get()
        tag = tag_entry.get()
        logging.debug(f"Building image with name: {image_name} and tag: {tag}")
        try:
            docker_client.images.build(path=dockerfile_path, tag=f"{image_name}:{tag}")
            logging.info(f"Docker image {image_name}:{tag} built successfully.")
            messagebox.showinfo("Success", f"Docker image {image_name}:{tag} built successfully.")
        except docker.errors.BuildError as e:
            logging.error(f"Build failed: {e}")
            messagebox.showerror("Build Error", f"Build failed: {e}")
        except Exception as e:
            logging.error(f"Failed to build image: {e}")
            messagebox.showerror("Error", f"Failed to build image: {e}")
        build_window.destroy()

    build_window = tk.Toplevel(root)
    build_window.title("Build Docker Image")

    tk.Label(build_window, text="Image Name:").grid(row=0, column=0)
    image_name_entry = tk.Entry(build_window)
    image_name_entry.grid(row=0, column=1)

    tk.Label(build_window, text="Image Tag:").grid(row=1, column=0)
    tag_entry = tk.Entry(build_window)
    tag_entry.grid(row=1, column=1)

    submit_button = tk.Button(build_window, text="Submit", command=submit_build)
    submit_button.grid(row=2, column=0, columnspan=2)


def list_docker_images():
    logging.info("Listing Docker images.")
    try:
        images = docker_client.images.list()
        image_list = "\n".join([", ".join(image.tags) for image in images if image.tags])
        logging.debug(f"Found Docker images: {image_list}")
        messagebox.showinfo("Docker Images", image_list if image_list else "No images found.")
    except Exception as e:
        logging.error(f"Failed to list Docker images: {e}")
        messagebox.showerror("Error", f"Failed to list Docker images: {e}")


def list_running_containers():
    logging.info("Listing running Docker containers.")
    try:
        containers = docker_client.containers.list()
        container_list = "\n".join([f"{container.id[:12]} - {container.name}" for container in containers])
        logging.debug(f"Running containers: {container_list}")
        messagebox.showinfo("Running Containers", container_list if container_list else "No containers running.")
    except Exception as e:
        logging.error(f"Failed to list running containers: {e}")
        messagebox.showerror("Error", f"Failed to list running containers: {e}")


def stop_container():
    logging.info("Stop Container function initiated.")
    try:
        containers = docker_client.containers.list()
        if not containers:
            logging.info("No running containers to stop.")
            messagebox.showinfo("Stop Container", "No running containers to stop.")
            return

        stop_window = tk.Toplevel(root)
        stop_window.title("Stop Container")

        tk.Label(stop_window, text="Select Container to Stop:").grid(row=0, column=0)
        container_var = tk.StringVar(value=containers[0].id)

        for i, container in enumerate(containers):
            tk.Radiobutton(stop_window, text=f"{container.id[:12]} - {container.name}", variable=container_var,
                           value=container.id).grid(row=i + 1, column=0)

        def submit_stop():
            try:
                container = docker_client.containers.get(container_var.get())
                container.stop()
                logging.info(f"Container {container.name} stopped successfully.")
                messagebox.showinfo("Success", "Container stopped successfully.")
            except Exception as e:
                logging.error(f"Failed to stop container: {e}")
                messagebox.showerror("Error", f"Failed to stop container: {e}")
            stop_window.destroy()

        submit_button = tk.Button(stop_window, text="Stop", command=submit_stop)
        submit_button.grid(row=len(containers) + 1, column=0)
    except Exception as e:
        logging.error(f"Failed to stop container: {e}")
        messagebox.showerror("Error", f"Failed to stop container: {e}")


def search_image():
    logging.info("Search Docker Image function initiated.")
    def submit_search():
        image_name = image_entry.get()
        logging.debug(f"Searching for Docker image with name: {image_name}")
        images = docker_client.images.list()
        found = False

        for image in images:
            for tag in image.tags:
                if image_name.lower() in tag.lower():
                    logging.info(f"Image found: {tag}")
                    messagebox.showinfo("Image Found", f"Image: {tag}")
                    found = True
                    break
            if found:
                break

        if not found:
            logging.info("Image not found.")
            messagebox.showinfo("Search Result", "Image not found.")
        search_window.destroy()

    search_window = tk.Toplevel(root)
    search_window.title("Search Docker Image")

    tk.Label(search_window, text="Enter Image Name:").grid(row=0, column=0)
    image_entry = tk.Entry(search_window)
    image_entry.grid(row=0, column=1)

    submit_button = tk.Button(search_window, text="Search", command=submit_search)
    submit_button.grid(row=1, column=0, columnspan=2)


def search_image_dockerhub():
    logging.info("Search DockerHub function initiated.")

    def submit_search_hub():
        image_name = image_entry.get()
        try:
            command = ["docker", "search", image_name]
            result = subprocess.run(command, capture_output=True, text=True)
            logging.info(f"DockerHub search results: {result.stdout}")
            messagebox.showinfo("Search DockerHub", result.stdout or "No results found.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to search DockerHub: {e}")
            messagebox.showerror("Error", f"Failed to search DockerHub: {e}")
        search_hub_window.destroy()

    search_hub_window = tk.Toplevel(root)
    search_hub_window.title("Search DockerHub")

    tk.Label(search_hub_window, text="Enter Image Name:").grid(row=0, column=0)
    image_entry = tk.Entry(search_hub_window)
    image_entry.grid(row=0, column=1)

    submit_button = tk.Button(search_hub_window, text="Search", command=submit_search_hub)
    submit_button.grid(row=1, column=0, columnspan=2)


def download_image():
    logging.info("Download Docker Image function initiated.")

    def submit_download():
        image_name = image_entry.get()
        try:
            docker_client.images.pull(image_name)
            logging.info(f"Downloaded Docker image: {image_name}")
            messagebox.showinfo("Success", f"Image {image_name} downloaded successfully.")
        except docker.errors.APIError as e:
            logging.error(f"Failed to download image: {e}")
            messagebox.showerror("Error", f"Failed to download image: {e}")
        download_window.destroy()

    download_window = tk.Toplevel(root)
    download_window.title("Download Docker Image")

    tk.Label(download_window, text="Enter Image Name:").grid(row=0, column=0)
    image_entry = tk.Entry(download_window)
    image_entry.grid(row=0, column=1)

    submit_button = tk.Button(download_window, text="Download", command=submit_download)
    submit_button.grid(row=1, column=0, columnspan=2)

def run_container():
    """Run a Docker container from an existing image."""
    logging.info("Run Docker Container function initiated.")
    def submit_run():
        image_name = image_entry.get()
        container_name = container_name_entry.get()
        logging.debug(f"Attempting to run container from image: {image_name}, with name: {container_name}")
        try:
            # Run the container
            container = docker_client.containers.run(
                image_name,
                name=container_name if container_name else None,
                detach=True
            )
            logging.info(f"Container {container.name} is running.")
            messagebox.showinfo("Success", f"Container {container.name} is running.")
        except docker.errors.ImageNotFound:
            logging.error("Image not found.")
            messagebox.showerror("Error", "Image not found. Please pull the image first.")
        except docker.errors.APIError as e:
            logging.error(f"Failed to run container: {e}")
            messagebox.showerror("Error", f"Failed to run container: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")
        run_window.destroy()

    run_window = tk.Toplevel(root)
    run_window.title("Run Docker Container")

    tk.Label(run_window, text="Enter Image Name:").grid(row=0, column=0)
    image_entry = tk.Entry(run_window)
    image_entry.grid(row=0, column=1)

    tk.Label(run_window, text="Container Name (Optional):").grid(row=1, column=0)
    container_name_entry = tk.Entry(run_window)
    container_name_entry.grid(row=1, column=1)

    submit_button = tk.Button(run_window, text="Run", command=submit_run)
    submit_button.grid(row=2, column=0, columnspan=2)


# Main GUI
root = tk.Tk()
root.title("Cloud Management System")

tk.Button(root, text="1. Create VM", command=create_vm_gui).pack(fill=tk.X)
tk.Button(root, text="2. Create Dockerfile", command=create_dockerfile).pack(fill=tk.X)
tk.Button(root, text="3. Build Docker Image", command=build_docker_image).pack(fill=tk.X)
tk.Button(root, text="4. List Docker Images", command=list_docker_images).pack(fill=tk.X)
tk.Button(root, text="5. List Running Containers", command=list_running_containers).pack(fill=tk.X)
tk.Button(root, text="6. Stop a Container", command=stop_container).pack(fill=tk.X)
tk.Button(root, text="7. Search for Docker Image", command=search_image).pack(fill=tk.X)
tk.Button(root, text="8. Search DockerHub", command=search_image_dockerhub).pack(fill=tk.X)
tk.Button(root, text="9. Download Docker Image", command=download_image).pack(fill=tk.X)
tk.Button(root, text="10. Run a Container", command=run_container).pack(fill=tk.X)


root.mainloop()
