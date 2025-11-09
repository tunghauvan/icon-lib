#!/usr/bin/env python3
"""
Script to generate XML for AWS icons in Draw.io.
Takes service name as argument, e.g., python generate_lambda_icon.py lambda
"""

import sys
import uuid
from difflib import get_close_matches
import urllib.request
import re

def fetch_aws_services_from_remote():
    """
    Fetch list of AWS services from Draw.io source on GitHub.
    Parse Sidebar-AWS4.js file to extract resIcon and fillColor.
    """
    url = "https://raw.githubusercontent.com/jgraph/drawio/refs/heads/dev/src/main/webapp/js/diagramly/sidebar/Sidebar-AWS4.js"
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
        
        # Regex to find resIcon patterns: resIcon=' + gn + '.service_name'
        # gn is 'mxgraph.aws4'
        resicon_pattern = r"resIcon=\s*'\s*\+\s*gn\s*\+\s*'\s*\.\s*([a-zA-Z_]+)"
        resicons = set(re.findall(resicon_pattern, content))
        
        # Regex to find nearby fillColor (approximate, may not be 100% accurate)
        # Find fillColor=... near resIcon
        services = {}
        for res in resicons:
            # Find fillColor in the same context (near resIcon)
            # Use regex to find fillColor before resIcon in the line
            pattern = rf"fillColor=([^;]+).*resIcon=\s*'\s*\+\s*gn\s*\+\s*'\s*\.{re.escape(res)}"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                fill_color = match.group(1).strip().strip("'\"")
            else:
                fill_color = "#F58534"  # Default color
            
            services[res] = {"resIcon": f"mxgraph.aws4.{res}", "fillColor": fill_color}
        
        return services
    except Exception as e:
        print(f"Error fetching from remote: {e}")
        return {}

# Load services from remote
AWS_SERVICES = fetch_aws_services_from_remote()

def generate_aws_icon_xml(service, x=2200, y=320, width=48, height=48, cell_id=None):
    """
    Generate XML string for AWS icon.

    Args:
        service (str): AWS service name (e.g., 'lambda')
        x, y, width, height: Same as before
        cell_id: Custom ID

    Returns:
        str: XML string for mxCell
    """
    if service not in AWS_SERVICES:
        raise ValueError(f"Service '{service}' is not supported. Available services: {list(AWS_SERVICES.keys())}")

    if cell_id is None:
        cell_id = f"{service}-{uuid.uuid4().hex[:8]}"

    config = AWS_SERVICES[service]
    res_icon = config["resIcon"]
    fill_color = config["fillColor"]

    # Template based on Draw.io source code
    xml_template = f'''<mxCell id="{cell_id}" value="" style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor={fill_color};strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon={res_icon};" vertex="1" parent="1">
  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry" />
</mxCell>'''

    return xml_template

def main():
    if not AWS_SERVICES:
        print("Cannot load services from remote. Check internet connection.")
        return

    if len(sys.argv) < 2:
        print("Usage: python generate_lambda_icon.py <service>")
        print(f"Supported services: {list(AWS_SERVICES.keys())}")
        return

    service = sys.argv[1].lower()
    try:
        print(f"Generating AWS {service.upper()} icon XML...")
        xml_output = generate_aws_icon_xml(service)
        # Extract only the style attribute
        style_match = re.search(r'style="([^"]*)"', xml_output)
        if style_match:
            print(style_match.group(1))
        else:
            print("Style not found")
    except ValueError as e:
        print(f"Error: {e}")
        # Suggest closest service
        closest = get_close_matches(service, AWS_SERVICES.keys(), n=1)
        if closest:
            print(f"Suggestion: Did you mean '{closest[0]}'?")

if __name__ == "__main__":
    main()