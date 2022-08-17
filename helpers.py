

def ceildiv(a, b):
    return -(a // -b)

def format_time(seconds):
	if seconds < 0:
		return f"-({format_time(-seconds)})"

	if seconds < 60:
		return f"{seconds:4.1f}s"

	minutes = int(seconds // 60)
	if minutes < 60:
		return f"{minutes:2d}m {seconds%60:4.1f}s"

	hours = int(minutes // 60)
	if hours < 24:
		return f"{hours:2d}h {minutes%60:2d}m {seconds%60:4.1f}s"

	days = int(hours // 24)
	return f"{days:2d}d {hours%24:2d}h {minutes%60:2d}m {seconds%60:4.1f}s"