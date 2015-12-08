#!/usr/bin/env python

import xml.etree.ElementTree

if __name__ == "__main__":
    html_tree = \
        xml.etree.ElementTree.parse("lindat-common/header.htm")
        #xml.etree.ElementTree.parse("lindat-common/header-services-standalone.htm")
    body = html_tree.find("body")
    #html_tree.find("title").text = "KER"

    my_content = \
        xml.etree.ElementTree.parse("demo.html")
    for element in my_content.find("body").getchildren():
        body.append(element)

    footer_tree = \
        xml.etree.ElementTree.parse("lindat-common/footer.htm")
        #xml.etree.ElementTree.parse("lindat-common/footer-services-standalone.htm")
    for element in footer_tree.find("body").getchildren():
        body.append(element)

    xml.etree.ElementTree.dump(html_tree)

