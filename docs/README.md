<p align="center">
  <img src="Logo with text.png" alt="SpotGazer" />
</p>

---

SpotGazer is your smart parking companion! This open-source project utilizes Python, Ultralytics YOLOv8, and Django to eliminate your pain in finding free parking spaces. 😤

With SpotGazer, you can monitor parking lot occupancy in real-time through video streams, efficiently utilizing each space. 📡 Our cutting-edge technology delivers accurate results, and our user-friendly web interface makes it accessible to all.

Join us in creating a greener, smarter future of parking! 🌍 🌿

## Installation
> **NOTE:** `Python 3` and the `venv` module must already be installed.

To install the system on Linux (based on Debian distribution), run the following commands in the console:

```bash
git clone https://github.com/AndriyKy/spot-gazer.git
cd spot-gazer
```

Create an `.env` file from [`.env.sample`](../.env.sample), set the necessary variables, and run [`build`](../build.sh):

```bash
./build.sh
```

Then run SpotGazer:

```bash
python3 -m run
```

## Features
- All details about parking lot in every marker on a map: address, private/shared, paid/free, total spots, spots for the disabled, number of occupied spots.
- Switching to online broadcast of a parking lot.
- Ability to switch to Google Maps by clicking on the parking lot address.
- Asynchronous processing of video streams with a fixed recognition interval.
- Debug console.
- Approximate location detection based on a client IP.


## Contribution

Contributions to the **SpotGazer** project are welcomed and greatly appreciated. Whether you're a developer, a designer, or a documentation enthusiast, there are many ways you can contribute to this open-source project. Here's how you can get involved:

- 💻 **Code Contributions:** If you're a developer, you can contribute to the project by working on new features, fixing bugs, or improving the codebase. To get started, fork the repository, make your changes, and submit a pull request.

- 🐛 **Issue Reporting:** If you encounter a bug or have a feature request, please open an issue on our GitHub repository. Be sure to provide detailed information to help us understand the problem or your idea.

- 🎨 **Design Contributions:** Designers can contribute by improving the project's user interface, creating graphics, or enhancing the project's visual elements.

- 📖 **Documentation:** Help us improve project documentation by fixing errors, enhancing explanations, or adding new guides.

- ⭐ **Show your support:** If you find this project useful, simply starring it on GitHub is a great way to show your support.

- 🌐 **Localization:** If you're proficient in multiple languages, you can contribute by translating the project to make it more accessible to a wider audience.

We look forward to your contributions and are excited to build this project together. Let's make **SpotGazer** even better with your help! 🚀
