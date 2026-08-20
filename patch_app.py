import re
import sys

def patch_app_tsx():
    file_path = "src/app/App.tsx"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Uncomment the backend API fetch calls
    # The pattern is:
    # // const schoolId = tokenManager.getSchoolId();
    # // const result = await apiGet(...);
    # // setData(result);
    content = re.sub(
        r'// const schoolId = tokenManager.getSchoolId\(\);',
        r'const schoolId = "default"; // Mock tokenManager.getSchoolId() for now',
        content
    )
    content = re.sub(
        r'// const result = await apiGet\((.*?)\);',
        r'const result = await apiGet(\1);',
        content
    )
    content = re.sub(
        r'// const result = await apiGet<any\[\]>\((.*?)\);',
        r'const result = await apiGet<any[]>(\1);',
        content
    )
    content = re.sub(
        r'// const result = await apiGet<any>\((.*?)\);',
        r'const result = await apiGet<any>(\1);',
        content
    )
    content = re.sub(
        r'// setData\(result\);',
        r'setData(result);',
        content
    )
    
    # Remove the bad powershell replace artifact
    content = content.replace(
        '// Data will be fetched from API here`n        // setError("Backend API not yet implemented");',
        ''
    )

    # 2. Inject useSettings to make "School ERP" dynamic.
    # To be totally safe, we will just replace "School ERP" in PageHeader with a dynamic prop if possible,
    # or just use a custom event/global variable. Let's use localStorage for absolute safety 
    # without breaking React Hook rules in 50 components.
    
    content = content.replace(
        'subtitle="School ERP — Summary overview"',
        'subtitle={`${localStorage.getItem("school_name") || "Nambale High"} — Summary overview`}'
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Successfully patched App.tsx")

if __name__ == "__main__":
    patch_app_tsx()
