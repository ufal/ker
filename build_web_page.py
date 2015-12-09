#!/usr/bin/env python

import xml.etree.ElementTree

if __name__ == "__main__":
    html_tree = \
        xml.etree.ElementTree.parse("lindat-common/header-services-standalone.htm")
    body = html_tree.find("body")
    html_tree.find(".//title").text = "KER"

    jquery = xml.etree.ElementTree.Element('script',
        attrib={"type": "text/javascript",
                "src" : "http://ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"})
    jquery.text = " "

    script = xml.etree.ElementTree.Element('script',
        attrib={"type" : "text/javascript"})
    script.text = "\n"
    f_script = open('ker_web.js', 'r')
    for line in f_script:
        script.text += line
    f_script.close()

    html_tree.find(".//head").append(jquery)
    html_tree.find(".//head").append(script)

    my_content = \
        xml.etree.ElementTree.parse("demo.html")
    for element in my_content.find("body").getchildren():
        body.append(element)

    footer_tree = \
        xml.etree.ElementTree.parse("lindat-common/footer-services-standalone.htm")
    for element in footer_tree.find("body").getchildren():
        body.append(element)

    xml.etree.ElementTree.dump(html_tree)

