# issue-scanner

Provides scanning analysis software, PR license and copyright functions in a service-oriented manner, and supports Gitee, Github, Gitlab, http, and purl link input.


# License Compliance issues (rules baseline)

This rule is designed to help community developers understand the compliance issues that exist in the software. For project compliance, this rule is the minimum requirement for License compliance. License compliance issues include but are not limited to these. Listed below are some common license compliance issues.

| **issues**                               | **baseline**                                                                                                                                                                                                                                                                         | explain                                                                        |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1. The project lacks an overall license              | There is a description of the complete text of the License in the file under the root directory (license, readme, copyright, notice, etc.) or the first-level subdirectory (/License(s)/License, _Notice_/License, etc.).                                                                                                                               | The project license text content should ensure completeness                                           |
| 2. The license of the project spec file is not standardized     | The license name is clear and standardized, and does not create ambiguity.                                                                                                                                                                                                                                           | The license name of the project does not cause ambiguity, such as the license name is wrong, the license version number is not carried, etc. |
| 3. Lack of repo-level copyright statement         | Contain copyrights field description in any file in the root directory or level 1 subdirectory, including but not limited to the following files: License, copyright, readme, notice                                                                                                                                                     | repo-level Copyright statement clarity and standardization                                       |
| 4.The repo uses a license that is not FSF or OSI certified | Defined importable license list                                                                                                                                                                                                                                                       | It is recommended to use an FSF or OSI certified license, non-certified licenses are subject to review                |


# License Compliance Practice Guide (Best Practices)

This rule is intended to provide projects with good practice cases for License compliance and is a supplement to the License compliance baseline requirements. License compliance items include but are not limited to these. Listed below are some common license compliance items.

| **describe**                   | **Best Practices**                                                                                                                     |      |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --- |
| 1. License for the entire repo      | It is recommended to use one of the following two methods:<br> 1. Place a separate License file in the root directory. <br> 2. Place a separate complete License file in the Licenses/License subdirectory. |
| 2. License name            | Use unified format spdx-identifier                                                                                                  |
| 3. Repo-level Copyright Statement | It is recommended to use one of the following two methods:<br>1. Place a separate Copyright Notice file in the root directory. <br> 2. Place a separate complete Notice file in the Notice subdirectory.   |
| 4 License used by the repo     | All projects use licenses certified by FSF or OSI        

# License access list
License Access List Reference：
<https://compliance.openeuler.org/license-list>

---

[Back to Contents](../../README.md)
