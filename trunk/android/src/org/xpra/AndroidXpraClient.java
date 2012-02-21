package org.xpra;

import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;

import xpra.AbstractClient;
import xpra.ClientWindow;
import android.content.Context;
import android.os.Vibrator;
import android.util.Log;
import android.view.Display;
import android.view.KeyCharacterMap;
import android.view.KeyEvent;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.Toast;

public class AndroidXpraClient extends AbstractClient {

	public final String TAG = this.getClass().getSimpleName();

	protected XpraActivity context = null;
	protected LayoutInflater inflater = null;
	protected KeyCharacterMap keyCharacterMap = null;
	protected WeakHashMap<Integer,Toast> toasts = new WeakHashMap<Integer,Toast>();
	protected int keymapId = -1;

	@Override
	public void debug(String str) {
		if (DEBUG)
			Log.d(this.TAG, str);
	}

	@Override
	public void log(String str) {
		Log.i(this.TAG, str);
	}

	@Override
	public void error(String str) {
		Log.e(this.TAG, str);
	}

	@Override
	public void error(String str, Throwable t) {
		Log.e(this.TAG, str, t);
	}

	@Override
	public void warnUser(String message) {
		this.log(message);
		Toast.makeText(this.context.getApplicationContext(), message, Toast.LENGTH_LONG).show();
	}
	
	
	public AndroidXpraClient(XpraActivity context, InputStream is, OutputStream os) {
		super(is, os);
		this.context = context;
		this.inflater = LayoutInflater.from(context);
	}

	/**
	 * Override so we can call all packet methods via the main thread
	 * by posting them to the client's handler.
	 */
	@Override
	public void invokePacketMethod(Method m, Object[] params) {
		this.context.handler.post(new PacketMethodInvoker(m, params));
	}
	
	public class PacketMethodInvoker implements Runnable {
		private Method method = null;
		private Object[] params = null;
		public PacketMethodInvoker(Method method, Object[] params) {
			this.method = method;
			this.params = params;
		}
		@Override
		public void run() {
			AndroidXpraClient.this.doInvokePacketMethod(this.method, this.params);
		}
	}


	@Override
	public int getScreenWidth() {
		Display display = this.context.getWindowManager().getDefaultDisplay();
		return display.getWidth();
	}

	@Override
	public int getScreenHeight() {
		Display display = this.context.getWindowManager().getDefaultDisplay();
		return display.getHeight();
	}

	@Override
	public void run(String[] args) {
		new Thread(this).start();
	}

	@Override
	public void cleanup() {
		super.cleanup();
		//
	}

	@Override
	public Object getLock() {
		return this;
	}

	@Override
	public Map<String, Object> make_hello(String enc_pass) {
		Map<String, Object> caps = super.make_hello(enc_pass);
		if (this.keyCharacterMap == null) {
			this.loadCharacterMap(KeyCharacterMap.BUILT_IN_KEYBOARD); // VIRTUAL_KEYBOARD);
			this.add_keymap_props(caps);
		}
		return caps;
	}

	public void loadCharacterMap(int deviceId) {
		this.keyCharacterMap = KeyCharacterMap.load(deviceId);
		this.keymapId = deviceId;
	}

	public void send_keymap() {
		Map<String, Object> props = new HashMap<String, Object>(10);
		this.add_keymap_props(props);
		this.send("keymap-changed", props);
	}

	public void add_keymap_props(Map<String, Object> props) {
		props.put("modifiers", new String[0]);
		props.put("xkbmap_keycodes", AndroidKeyboardUtil.getAllKeycodes());
		// ["xkbmap_print", "xkbmap_query", "xmodmap_data",
		// "xkbmap_mod_clear", "xkbmap_mod_add", "xkbmap_mod_meanings",
		// "xkbmap_mod_managed", "xkbmap_mod_pointermissing",
		// "xkbmap_keycodes"]:
	}

	public List<String> getModifiers(KeyEvent event) {
		List<String> modifiers = new ArrayList<String>(8);
		// int mask = event.getMetaState();
		if (event.isShiftPressed())
			modifiers.add("shift");
		// if ((mask & KeyEvent.META_CTRL_ON) != 0) //if (event.isCtrlPressed())
		// modifiers.add("control");
		if (event.isSymPressed())
			modifiers.add("mod2");
		if (event.isAltPressed())
			modifiers.add("mod1");
		/*
		 * if (event.isMetaPressed()) modifiers.add("mod2"); if
		 * (event.isFunctionPressed()) modifiers.add("mod3"); if
		 * (event.isCapsLockOn()) modifiers.add("mod4"); if
		 * (event.isNumLockOn()) modifiers.add("mod5"); if
		 * (event.isScrollLockOn()) modifiers.add("mod5");
		 */
		return modifiers;
	}

	public void sendKeyAction(int wid, View v, int keyCode, KeyEvent event) {
		this.debug("sendKeyAction(" + wid + ", " + v + ", " + keyCode + ", " + event + ")");
		if (this.keymapId != event.getDeviceId()) {
			this.log("sendKeyAction(" + wid + ", " + v + ", " + keyCode + ", " + event + ") keymap has changed - updating server");
			this.loadCharacterMap(event.getDeviceId());
			this.send_keymap();
		}
		List<String> modifiers = this.getModifiers(event);
		int keyval = event.getScanCode();
		String keyname = AndroidKeyboardUtil.keyCodeName(keyCode);
		String x11Keyname = AndroidKeyboardUtil.x11KeyName(keyname);
		this.log("sendKeyAction(" + wid + ", " + v + ", " + keyCode + ", " + event + ") android keyname=" + keyname+", x11Keyname="+x11Keyname);
		this.send("key-action", wid, x11Keyname, event.getAction() == KeyEvent.ACTION_DOWN, modifiers, keyval, "", event.getKeyCode());
	}

	@Override
	protected ClientWindow createWindow(int id, int x, int y, int w, int h, Map<String, Object> metadata, boolean override_redirect) {
		// XpraWindow window = new XpraWindow(this.context, this, id, x, y, w,
		// h, metadata, override_redirect);
		XpraWindow window = (XpraWindow) this.inflater.inflate(R.layout.xpra_window, null); // this.context.mDragLayer);
		window.init(this.context, this, id, x, y, w, h, metadata, override_redirect);
		this.log("createWindow(" + id + ", " + x + ", " + y + ", " + w + ", " + h + ", " + metadata + ", " + override_redirect + ")=" + window);
		this.context.add(window);
		// this.context.mDragLayer.addView(window);
		return window;
	}

	@Override
	protected void process_bell(int wid, int device, int percent, int pitch, int duration, String bell_class, int bell_id, String bell_name) {
		Vibrator v = (Vibrator) this.context.getSystemService(Context.VIBRATOR_SERVICE);
		int d = Math.min(5000, Math.max(100, duration));
		this.log("process_bell(" + wid + ", " + device + ", " + percent + ", " + pitch + ", " + duration + ", " + bell_class + ", " + bell_id + ", "
				+ bell_name + ") using "+v+" for "+d+" ms");
		v.vibrate(d);
	}

	@Override
	protected void process_notify_show(int dbus_id, int nid, String app_name, int replaced_id, String app_icon, String summary, String body, int expire_timeout) {
		this.log("process_notify_show(" + dbus_id + ", " + nid + ", " + app_name + ", " + replaced_id + ", " + app_icon + ", " + summary + ", " + body + ", "
				+ expire_timeout + ")");
		String text = summary;
		if (body!=null && body.length()>0)
			text += "\n\n"+body;
		Toast toast = Toast.makeText(this.context.getApplicationContext(), text, Toast.LENGTH_SHORT);
		toast.show();
		this.toasts.put(nid, toast);
	}

	@Override
	protected void process_notify_close(int nid) {
		Toast toast = this.toasts.get(nid);
		if (toast!=null)
			toast.cancel();
	}
}
