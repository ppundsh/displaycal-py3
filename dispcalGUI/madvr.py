# -*- coding: utf-8 -*-

# See developers/interfaces/madTPG.h in the madVR package

import ctypes
import os
import _winreg

import localization as lang


# Search for madTPG on the local PC, connect to the first found instance
CM_ConnectToLocalInstance = 0
# Search for madTPG on the LAN, connect to the first found instance
CM_ConnectToLanInstance = 1
# Start madTPG on the local PC and connect to it
CM_StartLocalInstance = 2
# Search local PC and LAN, and let the user choose which instance to connect to
CM_ShowListDialog = 3
# Let the user enter the IP address of a PC which runs madTPG, then connect
CM_ShowIpAddrDialog = 4
# fail immediately
CM_Fail = 5


class MadTPG(object):

	""" Minimal madTPG controller class """

	def __init__(self):
		# We only expose stuff we might actually use.
		self._methodnames = ("ConnectEx", "Disable3dlut", "GetDeviceGammaRamp",
							 "SetDeviceGammaRamp", "SetOsdText",
							 "GetPatternConfig", "SetPatternConfig",
							 "ShowProgressBar", "SetProgressBarPos", "ShowRGB",
							 "ShowRGBEx", "Load3dlutFile", "Disconnect",
							 "Quit")

		# Find madHcNet32.dll
		clsid = "{E1A8B82A-32CE-4B0D-BE0D-AA68C772E423}"
		try:
			key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
								  r"CLSID\%s\InprocServer32" % clsid)
			value, valuetype = _winreg.QueryValueEx(key, "")
		except:
			raise RuntimeError(lang.getstr("madvr.not_found"))
		dllpath = os.path.join(os.path.split(value)[0], "madHcNet32.dll")
		if not value or not os.path.isfile(dllpath):
			raise OSError(lang.getstr("not_found", dllpath))
		self.mad = ctypes.windll.LoadLibrary(dllpath)

		try:
			# Set expected return value types
			for methodname in self._methodnames:
				getattr(self.mad, "madVR_%s" % methodname).restype = ctypes.c_bool

			# Set expected argument types
			self.mad.madVR_ShowRGB.argtypes = [ctypes.c_double] * 3
			self.mad.madVR_ShowRGBEx.argtypes = [ctypes.c_double] * 6
		except AttributeError:
			raise RuntimeError(lang.getstr("madvr.outdated"))

	def __del__(self):
		if hasattr(self, "mad"):
			self.disconnect()

	def __getattr__(self, name):
		# Instead of writing individual method wrappers, we use Python's magic
		# to handle this for us. Note that we're sticking to pythonic method
		# names, so 'disable_3dlut' instead of 'Disable3dlut' etc.

		# Convert from pythonic method name to CamelCase
		methodname = "".join(part.capitalize() for part in name.split("_"))

		# Check if this is a madVR method we support
		if methodname not in self._methodnames:
			raise AttributeError("%r object has no attribute %r" %
								 (self.__class__.__name__, name))

		# Call the method and return the result
		return getattr(self.mad, "madVR_%s" % methodname)

	def connect(self, method1=CM_ConnectToLocalInstance, timeout1=1000,
				method2=CM_ConnectToLanInstance, timeout2=3000,
				method3=CM_ShowListDialog, timeout3=0, method4=CM_Fail,
				timeout4=0, parentwindow=None):
		""" Find, select or launch a madTPG instance and connect to it """
		return self.mad.madVR_ConnectEx(method1, timeout1, method2, timeout2,
										method3, timeout3, method4, timeout4,
										parentwindow)

	def get_device_gamma_ramp(self):
		""" Calls the win32 API 'GetDeviceGammaRamp' """
		ramp = ((ctypes.c_ushort * 3) * 256)()
		result = self.mad.madVR_GetDeviceGammaRamp(ramp)
		return result and ramp

	def show_rgb(self, r, g, b, bgr=None, bgg=None, bgb=None):
		""" Shows a specific RGB color test pattern """
		if not None in (bgr, bgg, bgb):
			return self.mad.madVR_ShowRGBEx(r, g, b, bgr, bgg, bgb)
		else:
			return self.mad.madVR_ShowRGB(r, g, b)


if __name__ == "__main__":
	import config
	config.initcfg()
	lang.init()
	madtpg = MadTPG()
	if madtpg.connect(method3=CM_StartLocalInstance, timeout3=5000):
		madtpg.show_rgb(1, 0, 0)