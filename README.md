# NeuroController
**Jarvis College of Computing and Digital Media – DePaul University**

## Authors and Contributors
- Alexandru Iulian Orhean (aorhean@depaul.edu)  
- Huy Nguyen (hnguye83@depaul.edu)  
- Areena Mahek (amahek@depaul.edu)  
- Ankita Kiran Kshirsagar (akshirsa@depaul.edu)  
- Marija Stojanoska (mstojan1@depaul.edu)  
- Rushikesh Rajendra Suryawanshi (rsuryawa@depaul.edu)  

---

## Overview

**NeuroController** serves as the central controller and orchestrator for the [Neurobazaar Platform](https://github.com/neurobazaar). It manages datastore configurations, coordinates dataset uploads, fetch operations, and authenticates ByteBridge instances to enable secure, distributed folder access.  

Recent enhancements include:
- Secure registration of external ByteBridge instances
- Access token–based validation
- Live file fetching directly from remote folders without needing to upload datasets

---

## Requirements and Setup

Tested on:  
- **Python:** 3.13  
- **OS:** Ubuntu 24.04 LTS Server Edition  

### Environment Setup
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Program

### First-time Database Setup
```bash
python manage.py makemigrations nc_app
python manage.py migrate
```

### Start the Development Server
```bash
python manage.py runserver
```

The app will start at `http://127.0.0.1:8000/`.

---

## ByteBridge Integration Workflow

### 1. Neurocontroller Startup
Ensure the server is running on `http://<NC_IP>:8000`.  

### 2. User Logs in to Neurocontroller
The user logs in via `/login/`, and receives an **access token (JWT)**.

---

### 3. ByteBridge Registration
On the ByteBridge machine (e.g., Charmi’s laptop), use the script:
```bash
python send_bytebridge_connection_request.py
```
You will be prompted to enter:
- Neurocontroller IP and port
- JWT access token
- Full path to folder (e.g., `C:/Users/Charmi/Desktop/images`)
- ByteBridge IP and port (e.g., `192.168.1.106:8001`)

Upon success:
```
ByteBridge registered successfully.
```

---

### 4. Record Stored in BBInstances
Neurocontroller saves the following:
- `datastore_id`, `instance_id`
- `ip_address`, `port`, and `exposed_path`
- `access_key` (generated using secure HMAC)

---

## Fetching Files

When Neurocontroller needs to fetch a file:
```http
GET http://<ByteBridge_IP>:<port>/fetch_file/?access_key=<generated_key>&name=<filename>
```

**Example:**
```http
GET http://192.168.1.106:8001/fetch_file/?access_key=216847e303...&name=whirlpool.jpg
```

This serves the file directly from the registered ByteBridge folder.

---

## Testing

To verify:
1. Start both Neurocontroller and ByteBridge Django servers
2. Make sure both are on the same network
3. Use `curl` or your browser to access the fetch URL
4. The file will download automatically (with fix for file extensions)

---

## Security Measures

- All communication includes a signed access key
- Neurocontroller verifies tokens to prevent unauthorized ByteBridge access
- Future plans include periodic token expiry checks and public key exchange

---

## Folder and File Overview

| Location                          | File/Module                             | Purpose                                 |
|-----------------------------------|------------------------------------------|------------------------------------------|
| `nc_app/models.py`                | `BBInstances`                            | Stores registered ByteBridge metadata    |
| `nc_app/views.py`                 | `register_bytebridge_instance()`        | Handles POST requests from ByteBridge    |
| `send_bytebridge_connection_request.py` | External script                     | Registers ByteBridge to Neurocontroller  |
| `urls.py`                         | `api/register_bytebridge/`              | API endpoint route                        |

---

## Following Project Standards

This update adheres to the **Neurobazaar architecture standards**:
- Modular REST API integration
- Secure access with JWT
- Clear model-view separation in Django
- Expandable datastore registration system
